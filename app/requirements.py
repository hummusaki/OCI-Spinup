import shutil
import os

def check_oci_cli():
    if shutil.which("oci"):
        print("OCI is installed")
        return True
    else:
        print("OCI is not installed")
        choice = input("Install now? [y/n]: ").strip().lower() or "y"
        if choice = "y":
            os.system("curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.py -o install.py")
            code = os.system(f"{sys.executable} install.py")
            if code = 0 and shutil.which("oci"):
                print("OCI CLI installed.")
                return True
        print("OCI CLI Unavailable. Exiting.")
        return False
