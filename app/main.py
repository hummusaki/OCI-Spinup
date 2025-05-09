from requirements import check_oci_cli
import os, time, sys
import create_server 
import argparse
import logger

CONFIG_PATH = os.path.expanduser("~/.oci/config")

# check for OCI CLI installation
if not check_oci_cli():
    sys.exit(1)

def setup():
    print("Launching OCI Config wizard...")
    os.system("oci setup config")

    print("Waiting for config file...", end="", flush=True)
    for _ in range(10):
        if os.path.exists(CONFIG_PATH):
            print(" done.")
            break
        print(".", end="", flush = True)
        time.sleep(1)
    else:
        print("\nError: ~/.oci/config not found after 10 s.")
        sys.exit(1)
    
    if os.system("oci os ns get > /dev/null 2>&1") != 0:
        print("Error: OCI CLI cannot read namespace. Check ~/.oci/config credentials.")
        sys.exit(1)

def main():
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    print("Welcome to the Oracle Compute Instance Manager!")
    print("This tool will help you set up an Oracle Compute Instance.\n")

    # Check for existing config and if not, create one
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-config", action="store_true", help="Skip `oci setup config` step if you already have credentials")
    args = parser.parse_args()

    if not args.skip_config:
        setup()

    # invoke the API to create the instance
    try:
        create_server.main()
    except Exception as e:
        logger.exception("Error provisioning the server:")
        sys.exit(1)


if __name__ == "__main__":
    main()
