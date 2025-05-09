import os
import oci
from oci.apm_synthetics.models import availability_configuration
from oci.config import from_file
from oci.core import ComputeClient, VirtualNetworkClient
from oci.core.models import ingress_security_rule
from pip._vendor.distro import id

# ------------------
# Constants
# ------------------

DEFAULT_IMAGE_ID = "ocid1.image.oc1.us-sanjose-1.aaaaaaaaanqjjat5r3nlz4fks5fsrrh3rrem4yq3buhz5blyhh4cdmsscneq"
VARIANTS = {
    "1": ("VANILLA", "itzg/minecraft-server"),
    "2": ("PAPER",   "itzg/minecraft-server"),
    "3": ("FORGE",   "itzg/minecraft-server")
} # Todo: add neo-forge and fabric

#       Load OCI config
config = from_file()

# This gets Tenancy OCID, initializes ComputeClient and VirtualNetworkClient
def get_clients(config):
    tenancy_ocid = config.get("tenancy")
    compute_client = ComputeClient(config)
    vcn_client = VirtualNetworkClient(config)
    return tenancy_ocid, compute_client, vcn_client

# This looks for an existing VCN by name, if not found then creates one; returns VCN OCID
def get_or_create_vcn(vcn_client, compartment_id, display_name, cidr_block="10.0.0.0/16"):
    existing = oci.pagination.list_call_get_all_results(
        vcn_client.list_vcns,
        compartment_id = compartment_id
    ).data
    # Check for existing VCN
    for v in existing:
        if v.display_name == display_name:
            return v.id

    # Create a new VCN
    vcn_details = oci.core.models.CreateVcnDetails(
        compartment_id = compartment_id,
        display_name = display_name,
        cidr_block = cidr_block
    )
    vcn = vcn_client.create_vcn(vcn_details).data
    # Wait until vcn is up
    oci.wait_until(vcn_client, vcn_client.get_vcn(vcn.id), 'lifecycle_state', 'AVAILABLE')
    return vcn.id

#       Create or retreive subnet

# Looks for existing subnet, otherwise creates one; returns subnet OCID
def get_or_create_subnet(vcn_client, compartment_id, vcn_id, display_name="MinecraftSubnet", cidr_block = "10.0.1.0/24", availability_domain = None):
    existing = oci.pagination.list_call_get_all_results(
        vcn_client.list_subnets,
        compartment_id = compartment_id,
        vcn_id = vcn_id
    ).data
    for s in existing:
        if s.display_name == display_name:
            return s.id

    subnet_details = oci.core.models.CreateSubnetDetails(
        compartment_id = compartment_id,
        vcn_id = vcn_id,
        display_name = display_name,
        cidr_block = cidr_block,
        availability_domain = availability_domain
    )
    subnet = vcn_client.create_subnet(subnet_details).data
    oci.wait_until(vcn_client, vcn_client.get_subnet(subnet.id), 'lifecycle_state', 'AVAILABLE')
    return subnet.id

#       Open Minecraft Port

def add_minecraft_rule(vcn_client, compartment_id, vcn_id, minecraft_port=25565):
    vcn = vcn_client.get_vcn(vcn_id).data
    security_lists = [vcn.default_security_list_id] + list(vcn.secutiy_list_ids)

    for sl_id in security_lists:
        sl = vcn_client.get_security_lists(sl_id).data
        # Check for rule
        for rule in sl.ingress_security_rules:
            if rule.protocol == '6' and rule.tcp_options and \
            rule.tcp_options.destination_port_range.min == minecraft_port:
                return


        # Create new rule
        sl.ingress_security_rules.append(
            oci.core.models.IngressSecurityRule(
                protocol = "6",      # TCP
                source = "0.0.0.0/0",       # Anywhere
                tcp_options = oci.core.models.TcpOptions(
                    destination_port_range = oci.core.models.PortRange(
                        min=minecraft_port, max=minecraft_port
                    )
                )
            )
        )
        vcn_client.update_security_lists(
            sl_id,
            oci.core.models.UpdateSecurityListDetails(
                ingress_security_rules = sl.ingress.ingress_security_rules
            )
        )
        return

#        Launch server instance
def launch_instance(compute_client, compartment_id, subnet_id, image_id = DEFAULT_IMAGE_ID, ocpus=1, memory=4, display_name="MC-Server", variant="VANILLA", docker_image = None):
    user_data = f"""
        #cloud-config
        package_update: true
        packages:
            -docker
        runcmd:
            - systemcl start docker
            - docker run -d -p 25565:25565 --name mc -e EULA=TRUE -e TYPE={variant} {VARIANTS[[k for k,v in VARIANTS.items() if v[0]==variant][0][1]]}
    """

    details = oci.core.models.LaunchInstanceDetails(
        compartment_id = compartment_id,
        availability_domain = config.get('availability_domain'),
        shape = "VM.Standard.A1.Flex",
        shape_config = oci.core.models.LaunchInstanceShapeConfigDetails(ocpus = ocpus, memory_in_gbs = memory),
        display_name = display_name,
        metadata = {'user_data': user_data.encode('utf-8').hex()},
        source_details = oci.core.models.InstanceSourceViaImageDetails(image_id = image_id),
        create_vnic_details = oci.core.models.CreateVnicDetails(subnet_id = subnet_id, assign_public_ip = True)
    )

    compute_client.launch_instance(details)


# ---------------------
# Main exec function
# ---------------------
def main():
    tenancy, compute, vcn_client = get_clients(config)
    compartment_id = tenancy

    # Server tier selection
    print("Choose a server tier or enter custom specs:")
    print("  [1] Vanilla 4-player     → 1 OCPU / 2 GB RAM")
    print("  [2] Vanilla 8-player     → 1 OCPU / 4 GB RAM")
    print("  [3] Vanilla 16-player    → 2 OCPU / 6 GB RAM")
    print("  [4] Forge 4-player       → 2 OCPU / 8 GB RAM")
    print("  [5] Custom")
    tier = input("Enter choice [1-5], default: [2]: ") or "2"
    presets = {"1": (1,2), "2": (1,4), "3": (2,6), "4": (2,6)}
    if tier in presets:
        ocpus, memory = presets[tier]
    else:
        try:
            ocpus = int(input("Enter number of OCPUs (max 4): ") or 1)
            memory = int(input("Enter RAM in GB (Max 24): ") or 4)
        except ValueError:
            ocpus, memory = 1, 4
    # Enforce tier limits
    if ocpus > 4 or memory > 24:
        print("Exceeds free tier; defaulting to 1 OCPU/4GB RAM")
        ocpus, memory = 1, 4

    # MC Variant select
    print("Select server variant:")
    print(" [1] Vanilla")
    print(" [2] Paper")
    print(" [3] Forge")
    var_choice = str(input("Enter choice [1-3], default: [1]: ")) or "1"
    variant_tuple = VARIANTS.get(var_choice)
    if variant_tuple is None:
        variant_tuple = VARIANTS["1"]
    variant, docker_image = variant_tuple

    # Names and image

    user_vcn_name = input("VCN Name (default: MinecraftVCN): ") or "MinecraftVCN"
    instance_name = input("Istance Name (default: MC-Server): ") or "MC-Server"
    image_id = input("Enter OCI Image OCID (default: Oracle Linux 8.10): ") or DEFAULT_IMAGE_ID

    # Provisioning
    print("Creating or retreiving VCN...")
    vcn_id = get_or_create_vcn(vcn_client, compartment_id, display_name = user_vcn_name)
    print(f"VCN OCID: {vcn_id}")

    print("Creating or retrieving Subnet...")
    subnet_id = get_or_create_subnet(vcn_client, compartment_id, vcn_id)
    print(f"Subnet OCID: {subnet_id}")

    print("Adding Minecraft security rule...")
    add_minecraft_rule(vcn_client, compartment_id, vcn_id)

    print(f"Launching {variant} server with {ocpus} OCPUs and {memory}GB RAM...")
    launch_instance(
        compute, compartment_id, subnet_id,
        image_id = image_id,
        ocpus = ocpus,
        memory = memory,
        display_name = instance_name,
        variant = variant,
        docker_image = docker_image,
    )

    print("Done! Your Minecraft Server instance is launching.")