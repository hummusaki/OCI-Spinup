from requirements import check_oci_cli
import os, time, sys
import argparse
import logging

CONFIG_PATH = os.path.expanduser("~/.oci/config")

def setup():
    print("Launching OCI Config wizard...")
    os.system("oci setup config")

    print("Waiting for config file...", end="", flush=True)
    for _ in range(10):
        if os.path.exists(CONFIG_PATH):
            print(" done.")
            print("\n" + "="*60)
            print("!! MANUAL STEP REQUIRED !!")
            print("Your config and keys have been generated")
            print(f"Publick key location: {os.path.expanduser('~/.oci/oci_api_key_public.pem')}")
            print("\nYou MUST upload this public key to your Oracle Cloud Console -> User Settings -> Tokens and Keys")
            print("Otherwise the script will crash with a 401 NotAuthenticated error.")
            
            print("\nPress ENTER once you've uploaded the keys to continue")

            return True
        print(".", end="", flush=True)
        time.sleep(1)
    print("\nError: config not found after 10 s.")
    return False

def main():
    logging.basicConfig(level=logging.INFO)
    print("Welcome to Oracle Compute Instance Spinup.\n")

    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-config", action="store_true",
                        help="Skip `oci setup config` if you already have credentials")
    args = parser.parse_args()

    if not args.skip_config:
        # 1. Verify or install the OCI CLI first
        if not check_oci_cli():
            logging.error("Failed to install or locate OCI CLI.")
            sys.exit(1)
            
        # 2. Check if the config file exists; if not, run the setup wizard
        if not os.path.exists(CONFIG_PATH):
            if not setup():
                sys.exit(1)

    try:
        import create_server
        create_server.main()
    except Exception as e:
        logging.exception("Error provisioning the server:")
        sys.exit(1)

if __name__ == "__main__":
    main()