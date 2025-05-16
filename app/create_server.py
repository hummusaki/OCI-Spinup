#!/usr/bin/env python3
"""
create_server.py

Automates provisioning an OCI compute instance preconfigured
to run a Docker-based Minecraft server via the Python SDK.
"""

import base64
import json
import textwrap

import oci
from oci.config import from_file
from oci.core import ComputeClient, VirtualNetworkClient
from oci.exceptions import ServiceError
from oci.core.models import (
    CreateVnicDetails,
    InstanceSourceViaImageDetails,
    LaunchInstanceDetails,
    LaunchInstanceShapeConfigDetails
)

# ------------------------------
# Configuration Constants
# ------------------------------
DEFAULT_IMAGE_ID = (
    "ocid1.image.oc1.us-sanjose-1.aaaaaaaadig2pewp2tt5nbfqpcwsbcuwtcxt2m3ptjols3iwmfcfouygdvyq"
)
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

# ------------------------------
# 6. Launch the server instance
# ------------------------------
def launch_instance(
    compute_client,
    availability_domain,
    subnet_id,
    image_id,
    ocpus=1,
    memory_in_gbs=4,
    display_name="MC-Server",
    variant="VANILLA",
    docker_image="itzg/minecraft-server"
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
    # OCI SDK will do the Base64 for us if you pass the raw string,
    # but if you want to pre-encode, you can:
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

    print("# REQUEST PAYLOAD")
    print(json.dumps(oci.util.to_dict(details), indent=2))
    print("# END PAYLOAD")

    # Launch the instance
    return compute_client.launch_instance(
        launch_instance_details = details
    )

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

    # 3) Names / image / AD
    vcn_name  = input("VCN name (MinecraftVCN): ") or "MinecraftVCN"
    inst_name = input("Instance name (MC-Server): ") or "MC-Server"
    img_id     = input("Image OCID (Oracle Linux 8): ") or DEFAULT_IMAGE_ID

    ad = identity_client.list_availability_domains(TENANCY_OCID).data[0].name
    print(ad)

    # 4) Network setup
    print("Creating or retrieving VCN…")
    vcn_id = get_or_create_vcn(vcn_client, TENANCY_OCID, vcn_name)
    print(f"VCN OCID: {vcn_id}")

    print("Creating or retrieving Subnet…")
    subnet_id = get_or_create_subnet(
        vcn_client, TENANCY_OCID, vcn_id,
        availability_domain=ad
    )
    print(f"Subnet OCID: {subnet_id}")

    print("Adding Minecraft security rule…")
    add_minecraft_rule(vcn_client, TENANCY_OCID, vcn_id)

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
        docker_image=docker_image
    )

    print("Instance OCID:", resp.data.id)
    print("Done! Your Minecraft server is provisioning.")

if __name__ == "__main__":
    main()
