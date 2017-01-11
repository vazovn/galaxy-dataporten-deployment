# Dataporten deployment

This is a script for deploying dataporten authentication for galaxy via apache httpd / openidc. 

Usage:

    ./deploy.sh
    
## Prerequisites

### Dataporten application

You need to have the dataporten openid information ready. For development, you can do this yourself. On [https://dashboard.dataporten.no/](https://dashboard.dataporten.no/), you will need to register an application. 
After registering, you will find the Client ID and Secret ID under OAuth credentials.

The important fields are:

#### Redirect URI

This is a url only for contact between the httpd server and dataporten. The domain name has to be the exactly same domain name that are used for the service.

    https://[domain name]/callback
    
for example:

    https://lifeportal.uio.no/callback

#### Auth providers

Select which providers the portal will use.

#### Permissions

Should be set to:

- E-post
- OpenID Connect
- Profilinfo
- Bruker-ID

### Galaxy-register 

#### Administrators

For portals maintained by FT, FT should be added as an administrator.

## What it does

### Installs mod_auth_openidc

The script downloads and installs the rpm packages for mod_auth_openidc.

### Updates httpd.conf and ssl.conf

## To be implemented:

- Creation of SSL keys and correct placement of these