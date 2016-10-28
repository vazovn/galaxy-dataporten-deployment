#!/bin/bash

VER=v2.0.0
MOD_AUTH_OPENIDC=mod_auth_openidc-2.0.0-1.el7.centos.x86_64.rpm
CJOSE=cjose-0.4.1-1.el7.centos.x86_64.rpm

function install_mod_auth_openidc {
    wget https://github.com/pingidentity/mod_auth_openidc/releases/download/${VER}/${MOD_AUTH_OPENIDC}
    wget https://github.com/pingidentity/mod_auth_openidc/releases/download/${VER}/${CJOSE}
    sudo yum localinstall ${MOD_AUTH_OPENIDC}
    sudo yum localinstall ${CJOSE}
    rm ${MOD_AUTH_OPENIDC}
    rm ${CJOSE}

}

if [ "$1" == "-y" ]; then
    install=Y
    updatehttpdconf=Y
else
    read -p "Install mod_auth_openidc?" install
    read -p "Update /etc/httpd/conf/httpd.conf" updatehttpdconf
fi

case ${install} in
    [Yy]* ) 
        install_mod_auth_openidc
    ;;
esac

case ${updatehttpdconf} in
    [Yy]* ) 
    awk '/Supplemental configuration/ {
        <Location "/">
        RequestHeader set X-URL-SCHEME https
        </Location>
    
        <VirtualHost _default_:80>
          RewriteEngine on
            ReWriteCond %{SERVER_PORT} !^443$
          RewriteRule ^/(.*) https://%{HTTP_HOST}/$1 [NC,R,L]
      </VirtualHost>
      }
      { print }
      ' /etc/httpd/conf/httpd.conf
    ;;
esac
