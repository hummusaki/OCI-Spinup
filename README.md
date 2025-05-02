
# Overview

Automate the creation of Oracle Free-Tier instances for their cloud computing platform. Particularly useful if you want to create free and easy Minecraft servers.

# Installation
## Requirements
This requires Python 3.12 or higher.

You will also need OCI CLI, which can be found here for Windows: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm#InstallingCLI__windows

Or here for any other supported OS: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm#InstallingCLI

Finally, you will need a free Oracle account.
Create it here: https://www.oracle.com/cloud/sign-in.html?redirect_uri=https%3A%2F%2Fcloud.oracle.com%2F

## Oracle Setup
Once the OCI CLI is installed, it will then ask for a location for the Setup file, then an OCID, API Signing Key and a Tenancy OCID.


## OCIDs and API Signing Key
### **OCIDs**
Once you're on your dashboard, click on your user icon in the top right corner, then "User Settings".
Then, under User Information you will find your OCID, which you will enter as the User OCID.

For the Tenancy OCID, click on your user icon again, then click on "Tenancy: [Your Username]"; under Tenancy Information you will find your Tenancy OCID, copy it and enter it as the Tenancy OCID.
### **Region**
It will then ask for a region for the server; if you're on the West Coast (near the south) like I am, enter 71 for US-San Jose.
Otherwise find the region that will work best for you. It will start with Continent/Country -> City

### **API Keys**
It will ask you if you want to generate an RSA key pair, select `y`

`Enter` the questions as they pop up to use the default values, until you reach the one where it asks for a passphrase:

**I recommend entering `N/A`**, which acts as a no-password setting. It will then ask it again, re-enter `N/A`.

Take note of where the keys are generate, it will usually be something like `C:\Users\userName\.oci\`

Navigate to your user icon on the top right again, then select User Settings, scroll down until you see "API Keys" on the left bar, click "Add API Key", and then "Choose public Key".

When you select your file, navigate to that directory that you took note of earlier and upload `oci_api_key_public.pem`, then click Add then Close at the button.
