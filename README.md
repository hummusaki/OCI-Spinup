<p align="center">
  <a href="https://gabmort.me/">
    <img src="https://gabmort.me/assets/m2.png" width="75"/>
  </a>
</p>
<h1 align="center">OCI-Spinup</h1>
<h3 align="center">Oracle Instance Automation</h3>
Automate the creation of Oracle Free-Tier instances for their cloud computing platform. Particularly useful if you want to create free and easy Minecraft servers.

# Features
* **Zero Touch Provisioning**: Queries Oracle to find the most recent ARM image for your region
* **Automatic Network Routing**: Automatically creates Virtual Cloud Networks, Subnets, Internet Gateways, and opens the `25565` port for Minecraft server usage
* **Docker Deployment**: Installs Docker and spins up a Vanilla / Paper / Forge server as soon as the instance boots

# Requirements
**Python 3.12 or higher**

You will need [OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm#InstallingCLI) and a free [Oracle account](https://www.oracle.com/cloud/sign-in.html?redirect_uri=https%3A%2F%2Fcloud.oracle.com%2F) with a connected credit card.

# Quick Start
```shell
git clone https://github.com/hummusaki/OCI-Spinup.git
cd OCI-Spinup/app
pip install oci
python main.py
```

# Config Guide

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
Then, under User Information you will find your OCID, this will be your **User OCID**.
#### Tenancy OCID
For the Tenancy OCID, click on your user icon again, then click on "Tenancy: [Your Username]".<br>
Under Tenancy Information you will find your **Tenancy OCID**.
### Region
As an example, if you're in Southern California, enter **71** for US-San Jose.
Otherwise find the region that will work best for you. It will start with Continent/Country -> City


