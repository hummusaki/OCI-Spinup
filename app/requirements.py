import shutil
import os
import sys

def check_oci_cli():
    # add default Oracle CLI path to current Python session
    user_bin = os.path.expanduser("~/bin")
    if user_bin not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f'{os.environ.get("PATH", "")}{os.pathsep}{user_bin}'
        
    if shutil.which("oci"):
        print("OCI is installed")
        return True
    else:
        print("OCI is not installed")
        choice = input("Install now? [y/n]: ").strip().lower() or "y"
        if choice == "y":
            print("Downloading OCI CLI installer ")
            os.system("curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.py -o install.py")
            print("Installing")
            code = os.system(f"{sys.executable} install.py --accept-all-defaults")
            if code == 0:
                if shutil.which("oci"):
                    print("\nOCI CLI installed.")
                    return True
                else:
                    print("\nOCI CLI was install, but executable wasn't found\nPlease run `exec -l $SHELL` and run this script again")
                    return False
        print("OCI CLI Unavailable. Exiting.")
        return False
