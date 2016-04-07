#!/usr/bin/env python

import os
import sys
import requests
import thread
import time


def monitor_stop_flag():
    while True:
        try:
            with open("/tmp/stop_flag", "r") as f:
                os._exit(0)
        except:
            time.sleep(1)

        
def get_index_from_requests_reply(reply):
    if reply.status_code != 200:
        print "ERROR: bad reply from consul"
        sys.exit(1)
    if 'X-Consul-Index' not in reply.headers:
        print "ERROR: bad reply from consul (missing index)"
        sys.exit(1)
    return reply.headers['X-Consul-Index']


def read_index_from_file():
    try:
        with open("/tmp/consul_index", "r") as f:
            return int(f.read().strip())
    except:
        return None


def write_index_to_file(index):
    if index is None:
        return
    try:
        with open("/tmp/consul_index", "w") as f:
             f.write("%i" % index)
    except:
        pass


CONSUL = os.environ['CONDRI_HAPROXY_CONSUL']
SERVICE_NAME = os.environ['CONDRI_HAPROXY_SERVICE_NAME']
WAIT = 30

thread.start_new_thread(monitor_stop_flag, ())

url1 = "http://%s/v1/health/checks/%s" % (CONSUL, SERVICE_NAME)
index1 = read_index_from_file()

if index1 is None:
    reply1 = requests.get(url1)
    index1 = get_index_from_requests_reply(reply1)
    write_index_to_file(index1)

url2 = "%s?index=%s&wait=%is" % (url1, index1, WAIT)
reply2 = requests.get(url2)
index2 = get_index_from_requests_reply(reply2)

if index1 != index2:
    write_index_to_file(index2) 
    os.system("make_haproxy_conf.sh RELOAD")
