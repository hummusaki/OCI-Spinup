import shutil
import os

def check_oci_cli():
    if shutil.which("oci"):
        print("OCI is installed")
    else:
        print("OCI is not installed")
        print("Would you like to install it now? Y/n")
        user_input = input().lower()
        if user_input == "y":
            os.system("Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.py' -OutFile 'install.py'")
            os.system("python install.py")
            print("OCI has been installed.")
        else:
            print("OCI installation skipped.")
