#!/usr/bin/env python

import argparse
import ConfigParser
import json
import subprocess

import datetime
import re
import psutil
import urlparse
import os
import io
import sys

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Read (or create) config file
config = ConfigParser.ConfigParser()
if os.path.isfile('/etc/galaxy_email.cfg'):
    config.read('/etc/galaxy_email.cfg')
if config.has_option('crediting', 'default_hours'):
    HOURS = config.get('crediting', 'default_hours')
else:
    HOURS = '200'
if config.has_option('log', 'file'):
    LOGFILENAME = config.get('log', 'file')
else:
    LOGFILENAME = '200'

10
# Database connection
engine = create_engine(config.get('db_gold', 'uri'))
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

class User(Base):
    __tablename__ = config.get('db_gold', 'table_name')
    id = Column(Integer, primary_key=True)
    uname = Column(String(20), index=True, unique=True)
    status = Column(String(20))
    projects = Column(String(200))
    mas_email = Column(String(100))
    ldap_email = Column(String(50))

    def __init__(self, uname, ldap_email, status=None, projects=None, mas_email=None ):
        self.uname = uname
        self.status = ""
        self.projects = ""
        self.mas_email = ""
        self.ldap_email = ldap_email

def popen_communicate(command):
    """

    :param command: gold command
    :type command: list
    :return: dictionary: {stdout, stderr, rc} (returncode)
    """
    with open(os.devnull, 'w') as devnull:
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sdata = p.communicate()
    return {'stdout': sdata[0],
            'stderr': sdata[1],
            'rc': p.returncode}


def add_remote_user_to_GOLD( email, provider=None ) :
    """
    At registration all users are added to GOLD: User is inserted to
    GOLD user DB and to gx_default (Galaxy default) project in GOLD.
    This is a new function for the common code only!!

    @:param email email address
    @:param provider idp provider type (feide, social) retrieved from dataporten
    """
    message = u""
    username = email.lower()
    user_info = []

    if provider[0] == "feide":
        description = 'Default FEIDE-Galaxy user'
    else:
        description = ":".join(provider)

    useradd_command = ['/opt/gold/bin/gmkuser', username, '-d', description]
    useradd = popen_communicate(useradd_command)

    ## If the user is already created:
    if useradd['rc'] == 74:
        return

    ## If goldd is not running:
    if useradd['rc'] == 22:
        log_message("Gold is not running. {} not added.".format(email))

    ## If the user is sucessfully created
    if useradd['rc'] == 0:
            ## Add user to default galaxy project gx_default, create account and credit the account with default CPU hours
            add_to_gx_default_command = ['/opt/gold/bin/gchproject', '--addUsers', username, 'gx_default']
            tmp = popen_communicate(add_to_gx_default_command)
            if tmp['rc'] != 0:
                log_message(tmp['stderr'])
                raise Exception()

            ## Add user to account 'username_gx_default' in project gx_default
            create_account_command = ["/opt/gold/bin/gmkaccount", '-p', 'gx_default', '-u', username, '-n', "{}_gx_default".format(username)]
            tmp = popen_communicate(create_account_command)
            if tmp['rc'] != 0:
                log_message(tmp['stderr'])
                raise Exception()

            ## Credit the account - CPU hours from config

            ## Get the account id
            get_account_id_command = ["/opt/gold/bin/glsaccount", "--show", "Id", "-n", "{}_gx_default".format(username)]
            tmp = popen_communicate(get_account_id_command)
            if tmp['rc'] != 0:
                log_message(tmp['stderr'])
                raise Exception()

            #for line in tmp['stdout'].readlines():
            account_info = tmp['stdout'].splitlines()[-1].split()
            account_id = account_info[0]
            # TODO remove

            ## Credit the account (in hours)
            credit_account_command = ["/opt/gold/bin/gdeposit", "-h", "-a", account_id, "-z", HOURS]
            tmp = popen_communicate(credit_account_command)
            if tmp['rc'] != 0:
                log_message(tmp['stderr'])
                raise Exception()
            log_message("Added {} to gx_default and credited {} hours to account id {}".format(username, HOURS, account_id))


def log_message(message):
    # If different location is needed, a different SELinux Type Enforcement module may be needed.
    #with io.open("/tmp/{}".format(logfilename), 'a') as logfile:
    with io.open("/var/log/goldhttpd/{}".format(LOGFILENAME), 'a') as logfile:
        message = u"" + datetime.datetime.now().isoformat() + ' ' + message + '\n'
        logfile.write(message)


def idp_provider_type_from_request(request):
    """
    :param request: String on the form email;dpid;http-request
    :return: tuple with idp provider type (first element: string with feide or social)
    """
    requestsplit = request.split(';', 2)
    if len(requestsplit) != 3:
        return "none"
    else:
        try:
            
            idp_provider_type = json.loads(urlparse.parse_qs(requestsplit[2])['acresponse'][0])['def'][0]
            
            ## This block inserts the users into the gold_db which contains their MAS projects
            if idp_provider_type[0] == "feide":
                
                ldap_email = requestsplit[0]
                uname =  json.loads(urlparse.parse_qs(requestsplit[2])['acresponse'][0])['userids'][0].split(":")[1].split("@")[0]

                user = User.query.filter_by(uname=uname).first()
                
                # if user exists, only the ldap_email may be changed 
                #(for uio users the ldap_email will be updated from ulrik to real ldap_email at first login)
                if user :
                    if user.ldap_email != ldap_email :
                        user.ldap_email = ldap_email
                        db_session.add(user)    
                        db_session.commit()
                    else :
                        pass
                    
                # insert a new user with the two values below
                # status, projects and mas_email come via cron script in the night
                else:
                    user = User(uname, ldap_email)
                    db_session.add(user)    
                    db_session.commit()
            
            else :
            
                # If users are not feide but social, their mas data will be populated directly by the cron script
                pass

        except:
            idp_provider_type = ("unknown",)
            
        return idp_provider_type


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", dest='email')
    parser.add_argument("-r", dest='request')
    args = parser.parse_args()
    log_message("Checking {}".format(args.email))
    add_remote_user_to_GOLD(args.email, idp_provider_type_from_request(args.request))
