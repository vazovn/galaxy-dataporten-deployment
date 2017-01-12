#!/usr/bin/env python

import argparse
import json
import subprocess
import re
import psutil
import urlparse

def add_remote_user_to_GOLD( email, provider=None ) :
    """
    At registration all users are added to GOLD: User is inserted to
    GOLD user DB and to gx_default (Galaxy default) project in GOLD.
    This is a new function for the common code only!!

    @:param email email address
    @:param provider idp provider type (feide, social) retrieved from dataporten
    """

    message = ""
    username = email
    user_info = []

    if provider[0] == "feide":
        description = 'Default FEIDE-Galaxy user'
    else:
        description = ":".join(provider)

    useradd_command = "sudo /opt/gold/bin/gmkuser %s -d \"%s\" " % (username, description)
    p = subprocess.Popen(useradd_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()

    ## Do not proceed if the user exists!!
    for line in p.stdout.readlines():
       if re.search("User already exists",line) :
            message = "User %s already exists in the GOLD DB!" % username
            return message

    ## Check if user has been added to GOLD DB
    user_check_command = "sudo /opt/gold/bin/glsuser -u %s " % username
    p = subprocess.Popen(user_check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.wait()

    for line in p.stdout.readlines():
        if re.search(username,line) :
            user_info = line.split()

    ## If the user is sucessfully created
    if user_info[0] == username and user_info[1] == 'True' :

            ## Add user to default galaxy project gx_default, create account and credit the account with default CPU hours
            add_to_gx_default_command = "sudo /opt/gold/bin/gchproject --addUsers %s gx_default " % username
            p = subprocess.Popen(add_to_gx_default_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()

            for line in p.stdout.readlines():
                if re.search("Successfully",line) :
                    message = "Remote user %s added successfully to GOLD DB and the default portal project (gx_galaxy) only.\n" % username
                    #print "Feide user %s added successfully to GOLD DB and the default portal project (gx_galaxy) only." % username

            ## Add user to account 'username_gx_default' in project gx_default
            create_account_command = "sudo /opt/gold/bin/gmkaccount -p gx_default -u %s -n \"%s_gx_default\"" % (username,username)
            p = subprocess.Popen(create_account_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()

            for line in p.stdout.readlines():
                if re.search("Successfully created",line) :
                    message = message +  "Created account in default portal project (gx_galaxy) for remote user %s. \n" % username
                    #print "Created account in gx_default for remote user %s." % username
            ## Credit the account - 200 CPU hours

            ## Get the account id
            get_account_id_command = "sudo /opt/gold/bin/glsaccount --show Id -n %s_gx_default" % username
            p = subprocess.Popen(get_account_id_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
            account_id = ''
            account_info = []
            for line in p.stdout.readlines():
                  account_info = line.split()
            account_id = account_info[0]

            ## Credit the account (in hours)
            credit_account_command = "sudo /opt/gold/bin/gdeposit -h -a %s -z 200" % account_id
            p = subprocess.Popen(credit_account_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()

            for line in p.stdout.readlines():
                if re.search("Successfully deposited",line) :
                    message = message +  "Credited account %s_gx_default for remote user %s in default portal project (gx_galaxy).\n" % (username,username)
                    message = message + line
                    #print "Credited account in gx_default for remote user %s." % username

            return message

    else :
        print "Failed to create a user in GOLD"

def check_if_gold_exist():
    for pid in psutil.pids():
        p = psutil.Process(pid)
        if p.name() == "goldd":
            return True

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
    if check_if_gold_exist():
        message = add_remote_user_to_GOLD(args.email, idp_provider_type_from_request(args.request))
        print message
    else:
        print idp_provider_type_from_request(args.request)
        print "User %s has not been added to GOLD! Add user manually. " % args.email
        pass


