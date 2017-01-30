#!/bin/bash

VER=v2.1.3
MOD_AUTH_OPENIDC=mod_auth_openidc-2.1.3-1.el7.centos.x86_64.rpm
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
    updatesslconf=Y
    installuserspy=Y
    fixfirewallandselinux=Y
else
    read -p "Install mod_auth_openidc? " installmod
    read -p "Update httpd.conf " updatehttpdconf
    read -p "Update ssl.conf " updatesslconf
    read -p "Install users.py" installuserspy
    read -p "Open ports and fix selinux issues? " fixfirewallandselinux
fi

echo "Before continuing, please read the information in README.md"
read -p "Dataporten Client ID: " dpclientid
read -p "Dataporten Client Secret: " dpclientsecret

case ${installmod} in
    [Yy]* ) 
        install_mod_auth_openidc
    ;;
esac

case ${installuserspy} in
    [Yy]* )
        sudo yum install postgresql-devel python-virtualenv
        sudo virtualenv /usr/local/.venv-galaxyemailusers
        sudo /usr/local/.venv-galaxyemailusers/bin/pip install sqlalchemy
        sudo /usr/local/.venv-galaxyemailusers/bin/pip install psycopg2
        sudo /usr/local/.venv-galaxyemailusers/bin/pip install psutil
        echo "copies users-script to /usr/local/galaxyemailusers.py"
        sudo cp users.py /usr/local/bin/galaxyemailusers.py
        echo "copies gold-script to /usr/local/adduser_to_gold.py"
        sudo cp adduser_to_gold.py /usr/local/bin/
        sudo /usr/local/.venv-galaxyemailusers/bin/python /usr/local/bin/galaxyemailusers.py --first
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
        randomstring=$(python -c 'import random, string; print "".join(random.choice(string.ascii_uppercase + string.digits) for n in range(random.randint(30,50)))')
        sed -i "s/CRYPTOPASSPHRASE/${randomstring}/" tmp.01.ssl.conf
        sed -i "s/HOSTNAME/${HOSTNAME}/" tmp.01.ssl.conf
        sudo sed -i.orig-$(date "+%y-%m-%d") -E '1 r tmp.01.ssl.conf' /etc/httpd/conf.d/ssl.conf
        rm tmp.01.ssl.conf

        echo "Adds service name to redirect in 02.ssl.conf"
        sed "s/GALAXYSERVICENAME/${galaxyservicename}/" 02.ssl.conf > tmp.02.ssl.conf

        echo "Adds galaxy proxy info"
        if grep --quiet 'VirtualHost _default_:443' /etc/httpd/conf.d/ssl.conf; then
            sudo sed -i -E '/VirtualHost _default_:443/r tmp.02.ssl.conf' /etc/httpd/conf.d/ssl.conf
        else
            echo "Line matching /VirtualHost _default_:443/ not found in ssl.conf."
            exit 1
        fi
        ;;
esac

case ${fixfirewallandselinux} in
    [Yy]* ) 
        echo "Open port 80 and 443"
        sudo firewall-cmd --permanent --add-port=443/tcp
        sudo firewall-cmd --permanent --add-port=80/tcp
        sudo firewall-cmd --reload

        echo "Fix selinux issues"
        sudo setsebool -P httpd_can_network_connect 1
        sudo setsebool -P httpd_can_network_relay 1
        sudo setsebool -P httpd_enable_homedirs 1

        # necessary?
        # sudo chcon -R -t httpd_sys_content_t /home/galaxy/galaxy/static/
        # sudo semanage fcontext -a -t httpd_sys_content_t /home/galaxy/galaxy/static
        # sudo restorecon -Rv /home/galaxy/galaxy/static
        sudo setsebool -P httpd_read_user_content 1

        # gold log
        sudo semanage fcontext -a -t httpd_sys_rw_content_t "/opt/gold/log(/.*)?"
        sudo restorecon -R /opt/gold/log

        # httpd-gold log
        sudo mkdir /var/log/goldhttpd
        sudo semanage fcontext -a -t httpd_sys_rw_content_t "/var/log/goldhttpd(/.*)?"
        sudo restorecon -R /var/log/goldhttpd

        # Apache restart
        sudo apachectl restart
    ;;
esac

