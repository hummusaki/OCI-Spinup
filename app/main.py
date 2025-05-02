import requirements
import os
import time
import create_server

# check for OCI CLI installation
requirements.check_oci_cli()

def main():
    print("Welcome to the Oracle Compute Instance Manager!")
    print("This tool will help you set up an Oracle Compute Instance.\n")

    # Generate Config
    os.system("oci setup config")

    # Wait, then check for config OK
    print("Checking configuration...")
    time.sleep(5)
    os.system("oci os ns get")

    # invoke the API to create the instance
    create_server.create_instance()


if __name__ == "__main__":
    main()
