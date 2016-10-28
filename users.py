#!/usr/bin/env python

import sys

table = {
}

def returnemail(request):
    requestsplit = request.strip().split(';')
    if requestsplit[0]:
        return requestsplit[0] + '\n'
    if len(requestsplit) > 1:
        if requestsplit[1] in table:
            return table[requestsplit[1]] + '\n'
    return "none\n"

while True:
    request = sys.stdin.readline()
    sys.stdout.write(returnemail(request))
    sys.stdout.flush()
