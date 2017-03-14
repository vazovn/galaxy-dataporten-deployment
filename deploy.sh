#!/bin/bash

# exit on all errors
error() {
    local sourcefile=$1
    local lineno=$2
    echo "Error on line ${lineno} in ${sourcefile}"
    exit 1
}
trap 'error "${BASH_SOURCE}" "${LINENO}"' ERR
# To ignore error from command, append this to command:
## 2>&1 || echo $?

mod_auth_openidc_url=https://github.com/pingidentity/mod_auth_openidc/releases/download/v2.1.5/mod_auth_openidc-2.1.5-1.el7.centos.x86_64.rpm
cjose_url=https://github.com/pingidentity/mod_auth_openidc/releases/download/v2.1.3/cjose-0.4.1-1.el7.centos.x86_64.rpm

# Check rhel major release
if [ $(lsb_release -rs | cut -f1 -d.) != "7" ]; then
    echo This script requires rhel7
    exit 1
fi

function install_mod_auth_openidc {
    wget ${mod_auth_openidc}
    wget ${cjose_url}
    sudo yum localinstall $(basename ${cjose_url})
    sudo yum localinstall $(basename ${mod_auth_openidc_url})
    sudo yum install mod_ssl
    rm -f $(basename ${mod_auth_openidc_url})
    rm -f $(basename ${cjose_url})

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
read -p "Public hostname: " public_hostname
read -p "Galaxy service name: " galaxyservicename
read -p "Maintenance page (for example operational log): " maint_page
read -p "Is this a report server?: [yN] " report_server

if [ "${report_server}" == "y" ]; then
	# http://www.uio.no/english/services/it/research/hpc/lifeportal-reports/unauthorized_access.html
	read -p "Set the URL for unauthorized access to a report server (applicable to report servers only): " reports_server_unauthorized
fi

case ${installmod} in
    [Yy]* ) 
        install_mod_auth_openidc
    ;;
esac

case ${installuserspy} in
    [Yy]* )
        sudo yum install postgresql-devel python-virtualenv
        if [ ! -d "/usr/local/.venv-galaxyemailusers" ]; then
            sudo virtualenv /usr/local/.venv-galaxyemailusers
        fi
        #sudo /usr/local/.venv-galaxyemailusers/bin/pip install --upgrade pip
        echo "copies users-script to /usr/local/galaxyemailusers.py"
        
        if [ "${report_server}" == "y" ]; then
			read -p "Please provide one email address (Feide) of a person authorized to view the report server data : " report_server_email_auth
			if [ ! -z "$report_server_email_auth" ]; then 
				sed -i "s/REPORT_SERVER_EMAIL_AUTH/${report_server_email_auth}/" users.py
			else
				echo "You must add at least one email address of a person authorised to see the reports-server!"
				echo "This info can be added later in the file /etc/galaxy_email.cfg. Multiple comma-separated emails are authorised."
				echo "Restart apache for the changes to become effective"
        fi
        
        sudo cp users.py /usr/local/bin/galaxyemailusers.py
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
        sed -i "s/HOSTNAME/${public_hostname}/" tmp.01.ssl.conf
        sudo sed -i.orig-$(date "+%y-%m-%d") -E '1 r tmp.01.ssl.conf' /etc/httpd/conf.d/ssl.conf
        rm tmp.01.ssl.conf

        echo "Adds service name to redirect in 02.ssl.conf"
        sed "s/GALAXYSERVICENAME/${galaxyservicename}/" 02.ssl.conf > tmp.02.ssl.conf
        sed -i "s%MAINTENANCE_PAGE%${maint_page}%" tmp.02.ssl.conf
        
        if [ "${report_server}" == "y" ]; then
			sed -i "s%REPORTS_UNAUTHORIZED%${reports_server_unauthorized}%" tmp.02.ssl.conf
		fi

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

        sudo semanage fcontext -a -t httpd_sys_content_t /home/galaxy/galaxy/static
        sudo restorecon -Rv /home/galaxy/galaxy/static
        sudo setsebool -P httpd_read_user_content 1

        # Apache restart
        sudo apachectl restart
    ;;
esac

