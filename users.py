#!/usr/bin/env python

import subprocess
import sys

table = {
}


def run_adduser_to_gold(email):
    if not email:
        pass
        # Write to log
    else:
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
        if requestsplit[1] in table:
            run_adduser_to_gold(table[requestsplit[1]])
            return table[requestsplit[1]] + '\n'
    return "none\n"

while True:
    request = sys.stdin.readline()
    sys.stdout.write(returnemail(request))
    sys.stdout.flush()
