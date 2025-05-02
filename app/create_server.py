import os
import subprocess

def create_subnet():
    # Create subnet

def create_instance():
    # Get user input
    print("If you are unsure about what you are doing, press Enter to use the default values when prompted.")
    print("What is the name of your instance?")
    display_name = input()
    if not display_name:
        display_name = "default_instance"

    print("How many OCPUs would you like to allocate?\n[Default: 1]\n[Recommended for Vanilla 16-player: 1 or 2]\n[Recommended for modded 8-player: 2 or 3]: ")
    num_ocpus = input()
    if not num_ocpus:
        num_ocpus = 1

    print("How much memory would you like to allocate?\n[Default: 6GB]\n[Recommended for Vanilla 16-player: 6GB or 8GB]\n[Recommended for modded 8-player: 10GB or 16GB]: ")
    memory = input()
    if not memory:
        memory = "4GB"

    # use default compartment
    compartment_id = "root"

    # use default shape
    shape = "VM.Standard.A1.Flex"

    # use default availability domain
    availability_domain = "AD1"


    # invoke the API to create the instance
    cmd = [
        "oci", "compute", "instance", "launch",
        "--availability-domain", availability_domain,
        "--compartment-id", compartment_id,
        "--shape", shape,
        "--shape-config", f'{{"ocpus": {num_ocpus}, "memoryInGBs": {memory}}}',
        "--image-id", image_id,
        "--subnet-id", subnet_id,
        "--display-name", display_name
    ]

    subprocess.run(cmd)


# USEFUL
# PS C:\Users\gabri> oci iam tenancy get --tenancy-id ocid1.tenancy.oc1..aaaaaaaav2ygxa2mk463cxxv6prttrcp7yv6fzsmvlnfhuta6wiw3yaezu5q
#{
#  "data": {
#    "defined-tags": {},
#    "description": "hummusaki",
#    "freeform-tags": {},
#    "home-region-key": "SJC",
#    "id": "ocid1.tenancy.oc1..aaaaaaaav2ygxa2mk463cxxv6prttrcp7yv6fzsmvlnfhuta6wiw3yaezu5q",
#    "name": "hummusaki",
#    "upi-idcs-compatibility-layer-endpoint": null
#  }
#}
