from requirements import check_oci_cli
import os, time, sys, subprocess
import create_server
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
            return True
        print(".", end="", flush=True)
        time.sleep(1)
    print("\nError: ~/.oci/config not found after 10 s.")
    sys.exit(1)

def main():
    logging.basicConfig(level=logging.INFO)
    print("Welcome to the Oracle Compute Instance Manager!\n")

    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-config", action="store_true",
                        help="Skip `oci setup config` if you already have credentials")
    args = parser.parse_args()

    if not args.skip_config:
        if not check_oci_cli():
            if not setup():
                sys.exit(1)

    try:
        create_server.main()
    except Exception as e:
        logging.exception("Error provisioning the server:")
        sys.exit(1)

if __name__ == "__main__":
    main()
