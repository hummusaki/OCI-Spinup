
# Overview

Automate the creation of Oracle Free-Tier instances for their cloud computing platform. Particularly useful if you want to create free and easy Minecraft servers.

# Installation
**This requires Python 3.12 or higher**

You will also need [OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm#InstallingCLI) and a free [Oracle account](https://www.oracle.com/cloud/sign-in.html?redirect_uri=https%3A%2F%2Fcloud.oracle.com%2F).

## OCIDs, Regions and API Signing Key
You'll need your API Keys, OCIDs, and your Region to continue:
### API Keys
After running main.py the program will ask you if you want to generate an RSA key pair, select `y`

`Enter` the questions as they pop up to use the default values, until you reach the one where it asks for a passphrase:

**I recommend entering `N/A`**, which acts as a no-password setting.

Take note of where the keys are generated, it will usually be something like `C:\Users\userName\.oci\`

Navigate to your user icon on the top right again, then select User Settings, scroll down until you see "API Keys" on the left bar, click "Add API Key", and then "Choose public Key".

When you select your file, navigate to that directory that you took note of earlier and upload `oci_api_key_public.pem`, then click Add then Close at the button.
### OCIDs
#### User OCID
Once you're on your dashboard, click on your user icon in the top right corner, then "User Settings".<br>
Then, under User Information you will find your OCID, this you will be the **User OCID**.
#### Tenancy OCID
For the Tenancy OCID, click on your user icon again, then click on "Tenancy: [Your Username]".<br>
Under Tenancy Information you will find your **Tenancy OCID**.
### Region
As an example, if you're in Southern California, enter **71** for US-San Jose.
Otherwise find the region that will work best for you. It will start with Continent/Country -> City


