#!/usr/local/.venv-galaxyemailusers/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2017 University of Oslo, Norway
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Cerebrum is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licences/>.

u"""
 This script is called by Apache HTTP Server RewriteMap.
 It handles authenticated users, where the IDP does not provide email address.
"""

import ConfigParser
import os
import subprocess
import sys

# Read (or create) config file
config = ConfigParser.ConfigParser()
if os.path.isfile('/etc/galaxy_email.cfg'):
    config.read('/etc/galaxy_email.cfg')
else:
    print "No config file found. Creating new"
    config.add_section('general')
    config.set('general', 'maintenance_stop', 'no')
    config.set('general', 'admins', '')
    
    # is this a report server?
    report_server = raw_input("Is this a report server? [yN] ")
    if report_server == "y":
		config.add_section('report_server')
		config.set('report_server', 'authorized_report_server_users', 'REPORT_SERVER_EMAIL' )
   
    config.add_section('log')
    config.set('log', 'file', 'reports-lifeportal.log')
    with open('/etc/galaxy_email.cfg', 'wb') as configfile:
        config.write(configfile)

# If run with any argument, exit after creating config
if len(sys.argv) > 1:
    print "Please fill out {}".format('/etc/galaxy_email.cfg')
    exit(0)

def return_email(request):
    """
    Splits string, and retrieves email address, either from string or from database.

    :param request: String of format email;dataporten-id
    :return: email address if found, else, the string none
    """
    requestsplit = request.strip().split(';')
    if requestsplit[0]:
        # if we get email from idp
        return requestsplit[0] + '\n'
    return "none\n"

MAINTENANCE_STOP = config.getboolean('general', 'maintenance_stop')
ADMINS = [e.strip() for e in config.get('general', 'admins').split(',')]
LOGFILENAME = config.get('log', 'file')

while True:
    request = sys.stdin.readline()
    email = return_email(request)
    
    # Section for report server only
    if config.has_section('report_server'):
		REPORT_SERVER_AUTHORIZED = [e.strip() for e in config.get('report_server', 'authorized_report_server_users').split(',')]
		if email[:-1] not in REPORT_SERVER_AUTHORIZED:
			sys.stdout.write('reports_unauthorized\n')
		else:
			sys.stdout.write(email)
		sys.stdout.flush()
			
    # Change this boolean and restart httpd for maintenance stop
    else :
		if MAINTENANCE_STOP and email[:-1] not in ADMINS:
			sys.stdout.write('maintenance\n')
		else:
			sys.stdout.write(email)
		sys.stdout.flush()
