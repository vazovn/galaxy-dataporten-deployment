#!/usr/local/.venv-galaxyemailusers/bin/python
## # /usr/bin/env python

import ConfigParser
import os.path
from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String, Boolean
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
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
    config.set('log', 'file', '')
    with open(sys.path[0] + '/config.cfg', 'wb') as configfile:
        config.write(configfile)

engine = create_engine(config.get('db', 'uri'))
db_session = scoped_session(sessionmaker(
    bind=engine))
# metadata = MetaData(db)
# users = Table('usersnew', metadata, autoload=True)
# Session = sessionmaker(bind=db)
# session = Session()
Base = declarative_base()
Base.query = db_session.query_property()

class User(Base):
    __tablename__ = 'usersnew'
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    email = Column(String(200))
    email_confirmed = Column(Boolean)
    conf_token = Column(String(200))
    # salt = Column(String(200))
    openid = Column(String(200), index=True, unique=True)

def find_user(dpid):
    user = db_session.query(User).filter_by(openid=dpid).first()
    return user

def run_adduser_to_gold(email):
    if os.path.isfile(sys.path[0] + '/adduser_to_gold.py') and email:
        subprocess.call(["python", sys.path[0] + "/adduser_to_gold.py", "-e", email])

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

if len(sys.argv) > 1:
    exit(0)

while True:
    request = sys.stdin.readline()
    sys.stdout.write(returnemail(request))
    sys.stdout.flush()
