#!/usr/bin/env python

import argparse
import subprocess
import re

def add_remote_user_to_GOLD( email, feide_username, idp ) :
    """
    At registration all users are added to GOLD: User is inserted to
    GOLD user DB and to gx_default (Galaxy default) project in GOLD.
    This is a new function for the common code only!!
    """

    message = ""
    username = email
    user_info = []
    description = 'Unspecified IdP'
    print "==========  Accounting.py  IDP =========", idp

    ## Add the user to GOLD DB
    if re.search("test-fe.cbu.uib.no", idp ):
        description = 'NELS IdP user'
    elif  re.search("feide.no", idp ):
        description = 'FEIDE IdP user'

    useradd_command = "sudo /opt/gold/bin/gmkuser %s -d \"%s\"" % (username,description)
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

    ## Nikolay USIT - LAP customization
    ## Check if the user is associated with a MAS project
    ## projects = _get_MAS_projects( feide_username)
    projects = []

    ## If the user is sucessfully created
    if user_info[0] == username and user_info[1] == 'True' :

        ## If the user is member of MAS projects and no 200 CPU hrs quota is allowed
        if len(projects) > 0 :
            proj_names = " ".join(projects)
            message = "A remote user %s has been added to the portal.</br>The user is a member of the project(s) %s and can only run jobs in these projects.\n" % (username,proj_names)
            #print "Feide user %s added successfully! User associated to Notur projects." % username
            return message

        else :
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
    # TODO
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", dest='email')
    args = parser.parse_args()
    if check_if_gold_exist():
        add_remote_user_to_GOLD(args.email, None, None)
    else:
        # log this
        pass


