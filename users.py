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
import os.path
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import subprocess
import sys

# Read (or create) config file
config = ConfigParser.ConfigParser()
if os.path.isfile(sys.path[0] + '/config.cfg'):
    config.read(sys.path[0] + '/config.cfg')
else:
    print "No config file found. Creating new"
    db_host = raw_input('Database host:')
    db_name = raw_input('Database name:')
    db_user = raw_input('Database user:')
    db_pass = raw_input('Database pass:')
    config.add_section('db')
    config.set('db', 'uri', 'postgresql://' + db_user
               + ':' + db_pass
               + '@' + db_host
               + '/' + db_name)
    config.set('db', 'table_name', 'users')
    config.add_section('log')
    config.set('log', 'file', '')
    with open(sys.path[0] + '/config.cfg', 'wb') as configfile:
        config.write(configfile)

# If run with any argument, exit after creating config
if len(sys.argv) > 1:
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


def run_adduser_to_gold(email):
    """
    Calls the script adduser_to_gold.py as a subprocess, if this file exist, and the email field is not empty.

    :param email: Email address
    """
    if os.path.isfile(sys.path[0] + '/adduser_to_gold.py') and email:
        subprocess.call(["python", sys.path[0] + "/adduser_to_gold.py", "-e", email])


def return_email(request):
    """
    Splits string, and retrieves email address, either from string or from database.

    :param request: String of format email;dataporten-id
    :return: email address if found, else, the string none
    """
    requestsplit = request.strip().split(';')
    if requestsplit[0]:
        # if we get email from idp
        run_adduser_to_gold(requestsplit[0])
        return requestsplit[0] + '\n'
    if len(requestsplit) > 1:
        user = find_user(requestsplit[1])
        if user and user.email and user.email_confirmed:
            run_adduser_to_gold(user.email)
            return user.email + '\n'
    return "none\n"

while True:
    request = sys.stdin.readline()
    sys.stdout.write(return_email(request))
    sys.stdout.flush()
