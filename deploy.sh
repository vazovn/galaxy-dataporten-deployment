#!/bin/bash

VER=v2.0.0
MOD_AUTH_OPENIDC=mod_auth_openidc-2.0.0-1.el7.centos.x86_64.rpm
CJOSE=cjose-0.4.1-1.el7.centos.x86_64.rpm

# Check rhel major release
if [ $(lsb_release -rs | cut -f1 -d.) != "7" ]; then
    echo This script requires rhel7
    exit 1
fi

function install_mod_auth_openidc {
    wget https://github.com/pingidentity/mod_auth_openidc/releases/download/${VER}/${CJOSE}
    wget https://github.com/pingidentity/mod_auth_openidc/releases/download/${VER}/${MOD_AUTH_OPENIDC}
    sudo yum localinstall ${CJOSE}
    sudo yum localinstall ${MOD_AUTH_OPENIDC}
    sudo yum install mod_ssl
    rm ${MOD_AUTH_OPENIDC}
    rm ${CJOSE}

}

if [ "$1" == "-y" ]; then
    install=Y
    updatehttpdconf=Y
else
    read -p "Install mod_auth_openidc? " installmod
    read -p "Update httpd.conf " updatehttpdconf
    read -p "Update ssl.conf " updatesslconf
fi

read -p "Dataporten Client ID: " dpclientid
read -p "Dataporten Client Secret: " dpclientsecret

case ${installmod} in
    [Yy]* ) 
        install_mod_auth_openidc
    ;;
esac

case ${updatehttpdconf} in
    [Yy]* ) 
        if grep --quiet 'Supplemental configuration' /etc/httpd/conf/httpd.conf; then
            sudo sed -i.orig-$(date "+%y-%m-%d") -E '/Supplemental configuration/r 01.httpd.conf' /etc/httpd/conf/httpd.conf
        else
            echo "Line matching /Supplemental configuration/ not found in httpd.conf"
            exit 1
        fi
    ;;
esac

case ${updatesslconf} in
    [Yy]* )
        echo "Adds DP info from 01.ssl.conf"
        sed "s/DPCLIENTID/${dpclientid}/" 01.ssl.conf > tmp.01.ssl.conf
        sed -i "s/DPCLIENTSECRET/${dpclientsecret}/" tmp.01.ssl.conf
        sed -i "s/HOSTNAME/${HOSTNAME}/" tmp.01.ssl.conf
        sudo sed -i.orig-$(date "+%y-%m-%d") -E '1 r tmp.01.ssl.conf' /etc/httpd/conf.d/ssl.conf
        rm tmp.01.ssl.conf

        echo "Adds galaxy proxy info"
        if grep --quiet 'VirtualHost _default_:443' /etc/httpd/conf.d/ssl.conf; then
            sudo sed -i -E '/VirtualHost _default_:443/r 02.ssl.conf' /etc/httpd/conf.d/ssl.conf
        else
            echo "Line matching /VirtualHost _default_:443/ not found in ssl.conf."
            exit 1
        fi
        echo "copies users-script to /usr/local/galaxyemailusers.py"
        sudo cp users.py /usr/local/bin/galaxyemailusers.py
        echo "copies gold-script to /usr/local/adduser_to_gold.py"
        sudo cp adduser_to_gold.py /usr/local/bin/
        ;;
esac


