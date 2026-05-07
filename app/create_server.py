#!/usr/bin/env python3
"""
create_server.py

Automates provisioning an OCI compute instance preconfigured
to run a Docker-based Minecraft server via the Python SDK.
"""

import base64
import textwrap
import time
import urllib3

from urllib3.exceptions import ProtocolError

import oci
from oci.config import from_file
from oci.core import ComputeClient, VirtualNetworkClient
from oci.exceptions import ServiceError, RequestException
from oci.core.models import (
    CreateVnicDetails,
    InstanceSourceViaImageDetails,
    LaunchInstanceDetails,
    LaunchInstanceShapeConfigDetails
)

# ------------------------------
# Configuration Constants
# ------------------------------
VARIANTS = {
    "1": ("VANILLA", "itzg/minecraft-server"),
    "2": ("PAPER",   "itzg/minecraft-server"),
    "3": ("FORGE",   "itzg/minecraft-server")
}

# ------------------------------
# 1. Load OCI configuration
# ------------------------------
config = from_file()  # reads ~/.oci/config
TENANCY_OCID = config["tenancy"]

# ------------------------------
# 2. Initialize clients
# ------------------------------
compute_client = ComputeClient(config)
vcn_client     = VirtualNetworkClient(config)
identity_client = oci.identity.IdentityClient(config)

# ------------------------------
# 3. Create or retrieve VCN
# ------------------------------
def get_or_create_vcn(vcn_client, compartment_id, display_name, cidr_block="10.0.0.0/16"):
    vcns = oci.pagination.list_call_get_all_results(
        vcn_client.list_vcns, compartment_id=compartment_id
    ).data

    # Return existing
    for v in vcns:
        if v.display_name == display_name:
            return v.id

    # Try to create
    try:
        new_vcn = vcn_client.create_vcn(
            oci.core.models.CreateVcnDetails(
                compartment_id=compartment_id,
                display_name=display_name,
                cidr_block=cidr_block
            )
        ).data
        oci.wait_until(vcn_client, vcn_client.get_vcn(new_vcn.id),
                       'lifecycle_state', 'AVAILABLE')
        return new_vcn.id

    except ServiceError as e:
        if e.status == 400 and e.code == "LimitExceeded":
            print(f"\n🚨 VCN limit reached ({len(vcns)} existing).")
            for idx, v in enumerate(vcns, start=1):
                print(f" [{idx}] {v.display_name} ({v.id})")
            choice = int(input(f"Select [1-{len(vcns)}]: ") or 1)
            return vcns[choice-1].id
        raise

# ------------------------------
# 4. Create or retrieve Subnet
# ------------------------------
def get_or_create_subnet(vcn_client, compartment_id, vcn_id,
                         display_name="MinecraftSubnet",
                         cidr_block="10.0.1.0/24",
                         availability_domain="AD-1"):
    subs = oci.pagination.list_call_get_all_results(
        vcn_client.list_subnets,
        compartment_id=compartment_id,
        vcn_id=vcn_id
    ).data

    for s in subs:
        if s.display_name == display_name:
            return s.id

    new_sub = vcn_client.create_subnet(
        oci.core.models.CreateSubnetDetails(
            compartment_id=compartment_id,
            vcn_id=vcn_id,
            display_name=display_name,
            cidr_block=cidr_block,
            availability_domain=availability_domain
        )
    ).data
    oci.wait_until(vcn_client, vcn_client.get_subnet(new_sub.id),
                   'lifecycle_state', 'AVAILABLE')
    return new_sub.id

# ------------------------------
# 5. Open Minecraft port
# ------------------------------
def add_minecraft_rule(vcn_client, compartment_id, vcn_id, port=25565):
    vcn = vcn_client.get_vcn(vcn_id).data
    sl_id = vcn.default_security_list_id
    sl = vcn_client.get_security_list(sl_id).data

    for rule in sl.ingress_security_rules:
        if (rule.protocol == "6"
            and rule.tcp_options
            and rule.tcp_options.destination_port_range.min == port):
            return  # already exists

    sl.ingress_security_rules.append(
        oci.core.models.IngressSecurityRule(
            protocol="6",
            source="0.0.0.0/0",
            tcp_options=oci.core.models.TcpOptions(
                destination_port_range=oci.core.models.PortRange(min=port, max=port)
            )
        )
    )
    vcn_client.update_security_list(
        sl_id,
        oci.core.models.UpdateSecurityListDetails(
            ingress_security_rules=sl.ingress_security_rules
        )
    )
    
# ----------------------------------
# 6. Create internet gateway + route
# ----------------------------------
def setup_internet_gateway(vcn_client, compartment_id, vcn_id):
    #check for existing gateways
    existing_igws = vcn_client.list_internet_gateways(compartment_id, vcn_id=vcn_id).data
    if existing_igws:
        igw_id = existing_igws[0].id
        print("Found existing internet gateway...")
    else:
        print("Creating internet gateway...")
        igw = vcn_client.create_internet_gateway(
            oci.core.models.CreateInternetGatewayDetails(
                compartment_id=compartment_id,
                vcn_id=vcn_id,
                is_enabled =True,
                display_name = "OCI-Spinup-IGW"
            )
        ).data
        igw_id = igw.id
        
    print("Updating route table")
    rt_id = vcn_client.get_vcn(vcn_id).data.default_route_table_id
    
    vcn_client.update_route_table(
        rt_id,
        oci.core.models.UpdateRouteTableDetails(
            route_rules=[
                oci.core.models.RouteRule(
                    network_entity_id=igw_id,
                    destination="0.0.0.0/0", #all external traffic
                    destination_type="CIDR_BLOCK"
                )
            ]
        )
    )


# -------------------
# 7. Fetch image OCID
# -------------------
def get_latest_arm_image(compute_client, compartment_id):
    print("Finding latest Oracle Linux 9 ARM image in your region")
    images = oci.pagination.list_call_get_all_results(
        compute_client.list_images,
        compartment_id=compartment_id,
        operating_system="Oracle Linux",
        operating_system_version="9",
        shape="VM.Standard.A1.Flex",
        sort_by="TIMECREATED",
        sort_order="DESC" #descending, so newest image is at index 0
    ).data
    
    if images:
        return images[0].id
    else:
        raise Exception("Couldn't find a valid Oracle Linux 9 ARM image in your region")


# -----------------------------
# 8. Launch the server instance
# -----------------------------
def launch_instance(
    compute_client,
    availability_domain,
    subnet_id,
    image_id,
    ocpus=1,
    memory_in_gbs=4,
    display_name="MC-Server",
    variant="VANILLA",
    docker_image="itzg/minecraft-server",
    max_retries=25
):
    """
    Wrapper to launch a VM.Standard.A1.Flex instance running Docker Minecraft.
    Uses global TENANCY_OCID for the compartment.
    """
    # Build cloud-init YAML
    raw = f"""
#cloud-config
package_update: true
packages:
  - docker
runcmd:
  - systemctl start docker
  - docker run -d -p 25565:25565 --name mc -e EULA=TRUE -e TYPE={variant} {docker_image}
"""
    user_data = textwrap.dedent(raw).lstrip("\n")
    b64_ud = base64.b64encode(user_data.encode()).decode()

    # Construct LaunchInstanceDetails
    details = LaunchInstanceDetails(
        compartment_id=TENANCY_OCID,
        availability_domain=availability_domain,
        shape="VM.Standard.A1.Flex",
        shape_config=LaunchInstanceShapeConfigDetails(
            ocpus=ocpus, memory_in_gbs=memory_in_gbs
        ),
        display_name=display_name,
        source_details=InstanceSourceViaImageDetails(
            source_type="image", image_id=image_id
        ),
        create_vnic_details=CreateVnicDetails(
            subnet_id=subnet_id, assign_public_ip=True
        ),
        metadata={"user_data": b64_ud}
    )

    # Fill in any missing optional attributes
    for prop in details.swagger_types:
        priv = f"_{prop}"
        if not hasattr(details, priv):
            setattr(details, priv, None)

    # Try to launch the instance
    attempt = 1
    while max_retries == -1 or attempt < max_retries:
        try:
            if attempt > 1:
                print(f"Attempt {attempt}: ")
            response = compute_client.launch_instance(
                launch_instance_details=details
            )
            print("Creation successful!")
            return response
        except ServiceError as e:
            if e.status == 500 and "Out of host capacity" in str(e.message):
                print(f"Oracle at capacity. Trying again in 30s...")
            else:
                raise
        except (RequestException, ProtocolError, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError) as neterr:
            print(f"Network hiccup ({neterr.__class__.__name__}). "
                  "Retrying in 30 s…")
        attempt+=1
        time.sleep(30)
    raise Exception("Exceeded maximum retries. Unable to launch instance.")

# ------------------------------
# Main execution
# ------------------------------
def main():
    # 1) Tier selection
    print("\nChoose server tier:")
    print(" [1] Vanilla 4-player → 1 OCPU / 2 GB")
    print(" [2] Vanilla 8-player → 1 OCPU / 4 GB")
    print(" [3] Vanilla 16-player → 2 OCPU / 6 GB")
    print(" [4] Forge 4-player   → 2 OCPU / 6 GB")
    print(" [5] Custom")
    tier = input("Choice [1-5, default 2]: ") or "2"
    presets = {"1": (1,2), "2": (1,4), "3": (2,6), "4": (2,6)}
    if tier in presets:
        ocpus, memory = presets[tier]
    else:
        ocpus = int(input("OCPUs (max 4): ") or 1)
        memory = int(input("RAM GB (max 24): ") or 4)
    if ocpus>4 or memory>24:
        print("Exceeds free tier; defaulting to 1 OCPU / 4 GB")
        ocpus, memory = 1, 4

    # 2) Variant
    print("\nSelect variant:")
    print(" [1] Vanilla")
    print(" [2] Paper")
    print(" [3] Forge")
    var = input("Choice [1-3, default 1]: ") or "1"
    variant, docker_image = VARIANTS.get(var, VARIANTS["1"])

    # 3) Names / AD
    vcn_name  = input("VCN name (MinecraftVCN): ") or "MinecraftVCN"
    inst_name = input("Instance name (MC-Server): ") or "MC-Server"

    ad = identity_client.list_availability_domains(TENANCY_OCID).data[0].name

    max_retries = input("If the server is full, retry amount [-1 for infinite, default 20]: ") or 20

    # 4) Network setup
    print("\nCreating or retrieving VCN…")
    vcn_id = get_or_create_vcn(vcn_client, TENANCY_OCID, vcn_name)
    print(f"VCN OCID: {vcn_id}")

    setup_internet_gateway(vcn_client, TENANCY_OCID, vcn_id)

    print("Creating or retrieving Subnet…")
    subnet_id = get_or_create_subnet(
        vcn_client, TENANCY_OCID, vcn_id,
        availability_domain=ad
    )
    print(f"Subnet OCID: {subnet_id}")

    print("Adding Minecraft security rule…")
    add_minecraft_rule(vcn_client, TENANCY_OCID, vcn_id)
    
    img_id = get_latest_arm_image(compute_client, TENANCY_OCID)

    # 5) Launch
    print(f"Launching {variant} server with {ocpus} OCPUs / {memory} GB…")
    resp = launch_instance(
        compute_client=compute_client,
        availability_domain=ad,
        subnet_id=subnet_id,
        image_id=img_id,
        ocpus=ocpus,
        memory_in_gbs=memory,
        display_name=inst_name,
        variant=variant,
        docker_image=docker_image,
        max_retries=int(max_retries)
    )

    print("Instance OCID:", resp.data.id)
    print("Done! Your Minecraft server is provisioning.")

if __name__ == "__main__":
    main()
