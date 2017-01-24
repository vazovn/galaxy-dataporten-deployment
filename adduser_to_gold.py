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

# Read (or create) config file
config = ConfigParser.ConfigParser()
if os.path.isfile(sys.path[0] + '/config.cfg'):
    config.read(sys.path[0] + '/config.cfg')
if config.has_option('crediting', 'default_hours'):
    hours = config.get('crediting', 'default_hours')
else:
    hours = '200'
if config.has_option('log', 'file'):
    logfilename = config.get('log', 'file')
else:
    logfilename = '200'

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
    username = email
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

            for line in tmp[0].readlines():
                  account_info = line.split()
            account_id = account_info[0]
            # TODO remove
            log_message(account_id)

            ## Credit the account (in hours)
            credit_account_command = ["/opt/gold/bin/gdeposit", "-h", "-a", account_id, "-z", hours]
            popen_communicate(credit_account_command)

    else :
        pass
        # log_message("Failed to create a user in GOLD")


def log_message(message):
    # If different location is needed, a different SELinux Type Enforcement module may be needed.
    with io.open("/var/log/httpd/{}".format(logfilename), 'a') as logfile:
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
        except:
            idp_provider_type = ("unknown",)
        return idp_provider_type


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", dest='email')
    parser.add_argument("-r", dest='request')
    args = parser.parse_args()
    add_remote_user_to_GOLD(args.email, idp_provider_type_from_request(args.request))
