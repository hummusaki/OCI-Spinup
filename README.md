<p align="center">
  <a href="https://gabmort.me/">
    <img src="https://gabmort.me/assets/m2.png" width="75"/>
  </a>
</p>
<h1 align="center">OCI-Spinup</h1>
<h3 align="center">Oracle Instance Automation</h3>
Automate the creation of Oracle Free-Tier instances for their cloud computing platform. Particularly useful if you want to quickly create a free Minecraft server.

<br>

> **❗️ IMPORTANT DISCLOSURE ❗️**
>
> Oracle's Always Free ARM servers are in **constant and incredibly high demand** and their instances are regularly at max capacity
>
> * **Free Option**: This program acts as an automated sniper, it'll likely hit an "Out of host capacity" error and loop for as long as you'd like it to in an attempt to find a slot; just leave it running as much as you can
> * **Fast Option**: To bypass this queue, you can upgrade your Oracle account to Pay-As-You-Go, so as long as you keep your server at or below the free limit (4 OCPUs, 24GB RAM, 200GB Boot Volume) you won't be charged, but Oracle will place a temporary $100 hold on your card


# Features
* **Sniper Mode**: Continuously loops to grab a free server the second hardware space becomes available 
* **Zero Touch Provisioning**: Queries Oracle to find the most recent ARM image for your region
* **Automatic Network Routing**: Automatically creates Virtual Cloud Networks, Subnets, Internet Gateways, and opens the `25565` port for Minecraft server usage
* **Docker Deployment**: Installs Docker and spins up a Vanilla / Paper / Forge server as soon as the instance boots

# Requirements
**Python 3.12 or higher**

A free [Oracle account](https://www.oracle.com/cloud/sign-in.html?redirect_uri=https%3A%2F%2Fcloud.oracle.com%2F) with a connected credit card (required by Oracle for identity verification).

# Quick Start
```shell
git clone https://github.com/hummusaki/OCI-Spinup.git
cd OCI-Spinup/app
python3 -m venv venv
source venv/bin/activate
pip install oci
python main.py
```

# Config Guide
You'll need your OCIDs, Region, and API Keys to continue

### 1: OCIDs
**User OCID**: 
Once you're on your dashboard, click on your user icon in the top right corner, then "User Settings", under User Information copy your OCID

**Tenancy OCID**: Click on your user icon again -> "Tenancy: [Your Username]", and copy that OCID

### 2: Follow the prompt
Paste your OCIDs when prompted, then the script will output 80+ regions; find the one with the city closest to you (e.g. us-sanjose-1) and type the corresponding number.

### 3: API Keys
When it asks you if you want to generate an RSA key pair, select `y`

`Enter` the questions as they pop up to use the default values, until it asks for a passphrase:

**I recommend entering `N/A`**, which acts as a no-password setting.

Take note of where the keys are generated, it will usually be something like `C:\Users\userName\.oci\`

### 4: CRITICAL, upload Public Key to Oracle

The process will pause after generating your keys, you *must* upload your Public Key to oracle before you can continue:

- Navigate to your user icon on the top right again, select User Settings, click the "Tokens and Keys" on the top bar, click "Add API Key", and then "Choose public Key".

- When selecting your file, navigate to the directory that you took note of earlier (the directory might be hidden, look up how to show hidden folders for your OS) and upload `oci_api_key_public.pem`, then click Add.

# Next steps
Once the program finds hardware space and provisions your instance, it'll break out of the waiting loop.

**From here**:
1.  Wait for the script to install Docker on your server
2. The terminal will output the server's new Public IP (it can also be accessed from Oracle's Cloud Dashboard)
3. Start up Minecraft, enter the IP address, and join your new server!
