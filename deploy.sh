#!/bin/bash

VER=v2.0.0
MOD_AUTH_OPENIDC=mod_auth_openidc-2.0.0-1.el7.centos.x86_64.rpm
CJOSE=cjose-0.4.1-1.el7.centos.x86_64.rpm

function install_mod_auth_openidc {
    wget https://github.com/pingidentity/mod_auth_openidc/releases/download/${VER}/${MOD_AUTH_OPENIDC}
    wget https://github.com/pingidentity/mod_auth_openidc/releases/download/${VER}/${CJOSE}
    sudo yum localinstall ${MOD_AUTH_OPENIDC}
    sudo yum install mod_ssl
    # sudo yum localinstall ${CJOSE}
    rm ${MOD_AUTH_OPENIDC}
    rm ${CJOSE}

}

if [ "$1" == "-y" ]; then
    install=Y
    updatehttpdconf=Y
else
    read -p "Install mod_auth_openidc?" installmod
    read -p "Update httpd.conf" updatehttpdconf
fi

read -p "Dataporten Client ID" dpclientid
read -p "Dataporten Client Secret" dpclientsecret

case ${installmod} in
    [Yy]* ) 
        install_mod_auth_openidc
    ;;
esac

case ${updatehttpdconf} in
    [Yy]* ) 
    gawk -i inplace -v INPLACE_SUFFIX=.original \
        '/Supplemental configuration/ {print "
        <Location \"/\">
        RequestHeader set X-URL-SCHEME https
        </Location>
    
        <VirtualHost _default_:80>
          RewriteEngine on
            ReWriteCond %{SERVER_PORT} !^443$
          RewriteRule ^/(.*) https://%{HTTP_HOST}/$1 [NC,R,L]
      </VirtualHost>
      "}1;
      { print }
      ' /etc/httpd/conf/httpd.conf

#    gawk -i inplace -v INPLACE_SUFFIX=.original \
#        '/## SSL Virtual Host Context/ { print "
#    OIDCResponseType \"code\"
#    OIDCProviderMetadataURL https://auth.dataporten.no/.well-known/openid-configuration
#    OIDCClientID " dpclientid "
#    OIDCClientSecret " dpclientsecret "
#    OIDCCryptoPassphrase openstack
#    OIDCRedirectURI https://geoaccessno-u01.hpc.uio.no/callback
#    #OIDCRemoteUserClaim email
#    OIDCScope \"openid email profile\"
#"}1
#    ' /etc/httpd/conf.d/ssl.conf
    ;;
esac
