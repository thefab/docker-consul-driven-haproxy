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

        
def get_index_from_requests_reply(mode, reply):
    if mode == 'services' and reply.status_code != 200:
        print "ERROR: bad reply from consul"
        sys.exit(1)
    if 'X-Consul-Index' not in reply.headers:
        print "ERROR: bad reply from consul (missing index)"
        sys.exit(1)
    return reply.headers['X-Consul-Index']


def read_index_from_file(mode, service_name):
    try:
        with open("/tmp/consul_index_%s_%s" % (mode, service_name), "r") as f:
            return int(f.read().strip())
    except:
        return None


def write_index_to_file(mode, service_name, index):
    if index is None:
        return
    try:
        with open("/tmp/consul_index_%s_%s" % (mode, service_name), "w") as f:
             f.write("%i" % index)
    except:
        pass


CONSUL = os.environ['CONDRI_HAPROXY_CONSUL']
MODE = "services"
if len(sys.argv) >= 3 and sys.argv[2] == 'kv':
    MODE = 'kv'
    SERVICE_NAME = '__kv'
else:
    SERVICE_NAME = sys.argv[1]
WAIT = 20

thread.start_new_thread(monitor_stop_flag, ())

if MODE == 'services':
    # mode = services
    url1 = "http://%s/v1/health/checks/%s" % (CONSUL, SERVICE_NAME)
    index1 = read_index_from_file(MODE, SERVICE_NAME)
    if index1 is None:
        reply1 = requests.get(url1)
        index1 = get_index_from_requests_reply(MODE, reply1)
        write_index_to_file(MODE, SERVICE_NAME, index1)
    url2 = "%s?index=%s&wait=%is" % (url1, index1, WAIT)
    reply2 = requests.get(url2)
    index2 = get_index_from_requests_reply(MODE, reply2)
else:
    # mode = kv
    url1 = "http://%s/v1/kv/%s" % (CONSUL, sys.argv[1])
    index1 = read_index_from_file(MODE, SERVICE_NAME)
    if index1 is None:
        reply1 = requests.get(url1)
        index1 = get_index_from_requests_reply(MODE, reply1)
        write_index_to_file(MODE, SERVICE_NAME, index1)
    url2 = "%s?index=%s&wait=%is" % (url1, index1, WAIT)
    reply2 = requests.get(url2)
    index2 = get_index_from_requests_reply(MODE, reply2)

if index1 != index2:
    return_code = os.system("make_haproxy_conf.sh RELOAD")
    if return_code == 0:
        write_index_to_file(MODE, SERVICE_NAME, index2) 
