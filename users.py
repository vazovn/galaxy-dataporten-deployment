#!/usr/bin/env python

import ConfigParser
import os.path

from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker
import subprocess
import sys

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
    config.add_section('log')
    config.set('file', '')
    with open(sys.path[0] + '/config.cfg', 'wb') as configfile:
        config.write(configfile)

db = create_engine(config.get('db', 'uri'))
metadata = MetaData(db)
users = Table('usersnew', metadata, autoload=True)
Session = sessionmaker(bind=db)

def find_user(dpid):
    user = Session.query.filter_by(openid=dpid).first()
    return user

def run_adduser_to_gold(email):
    if email:
        subprocess.call(["python", "adduser_to_gold.py", "-e", email])

def returnemail(request):
    # Apache sends this in format:
    # email;dataporten-id
    requestsplit = request.strip().split(';')
    if requestsplit[0]:
        # if we get email from idp
        run_adduser_to_gold(requestsplit[0])
        return requestsplit[0] + '\n'
    if len(requestsplit) > 1:
        user = find_user(requestsplit[1])
        if user and user.email:
            run_adduser_to_gold(user.email)
            return user.email + '\n'
    return "none\n"

while True:
    request = sys.stdin.readline()
    sys.stdout.write(returnemail(request))
    sys.stdout.flush()
