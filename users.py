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
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
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
    
    db_host = raw_input('Database host:')
    db_name = raw_input('Database name:')
    db_user = raw_input('Database user:')
    db_pass = raw_input('Database pass:')
    
    # run adduser to gold?
    run_adduser = raw_input("Run adduser to gold? [yN] ")
    # gold data
    if run_adduser == "y":
        gold_db_host = raw_input('GOLD database host:')
        gold_db_name = raw_input('GOLD database name:')
        gold_db_user = raw_input('GOLD database user:')
        gold_db_pass = raw_input('GOLD database pass:')
        config.set('general', 'run_adduser_to_gold', 1)
    else:
        config.set('general', 'run_adduser_to_gold', 0)
    
    config.add_section('db')
    config.set('db', 'uri', 'postgresql://' + db_user
               + ':' + db_pass
               + '@' + db_host
               + '/' + db_name)
    config.set('db', 'table_name', 'usersprod')
    
    # configure gold db
    config.add_section('db_gold')
    if run_adduser:
        config.set('db_gold', 'uri', 'postgresql://' + gold_db_user
                   + ':' + gold_db_pass
                   + '@' + gold_db_host
                   + '/' + gold_db_name)
    else:
        config.set('db_gold', 'uri', 'none')
    config.set('db_gold', 'mas_table_name', 'g_mas_projects')

    config.add_section('log')
    config.set('log', 'file', 'adduser_to_gold.log')
    config.add_section('crediting')
    config.set('crediting', 'default_hours', '200')
    with open('/etc/galaxy_email.cfg', 'wb') as configfile:
        config.write(configfile)

# If run with any argument, exit after creating config
if len(sys.argv) > 1:
    print "Please fill out {}".format('/etc/galaxy_email.cfg')
    exit(0)

# Database connection
engine = create_engine(config.get('db', 'uri'))
db_session = scoped_session(sessionmaker(
    bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class User(Base):
    __tablename__ = config.get('db', 'table_name')
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    email = Column(String(200))
    email_confirmed = Column(Boolean)
    conf_token = Column(String(200))
    openid = Column(String(200), index=True, unique=True)


def find_user(dpid):
    """
    Queries the database for a dataporten user

    :param dpid: string containing dataporten id.
    :return: user object (table row from database)
    """
    user = db_session.query(User).filter_by(openid=dpid).first()
    return user


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
    if len(requestsplit) > 1:
        user = find_user(requestsplit[1])
        if user and user.email and user.email_confirmed:
            return user.email + '\n'
    return "none\n"

MAINTENANCE_STOP = config.getboolean('general', 'maintenance_stop')
ADMINS = [e.strip() for e in config.get('general', 'admins').split(',')]
LOGFILENAME = config.get('log', 'file')

while True:
    request = sys.stdin.readline()
    email = return_email(request)
    # Change this boolean and restart httpd for maintenance stop
    if MAINTENANCE_STOP and email[:-1] not in ADMINS:
        sys.stdout.write('maintenance\n')
    else:
        sys.stdout.write(email)
    sys.stdout.flush()
