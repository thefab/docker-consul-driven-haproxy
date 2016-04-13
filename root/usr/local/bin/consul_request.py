#!/bin/env python

import os
import sys
import uuid
import json

def _consul_tuples(consul, service_name, only_passing=True, timeout=10, tags=[]):
    consul_cli = "timeout --signal=SIGKILL %i consul-cli --consul=%s" % (timeout, consul)
    random = str(uuid.uuid4())
    res = []
    try:
        os.system("%s health service %s >/tmp/%s" % (consul_cli, service_name, random))
        with open("/tmp/%s" % random, "r") as f:
            content = json.loads(f.read())
        os.unlink("/tmp/%s" % random)
    except:
        os.unlink("/tmp/%s" % random)
        return res
    for block in content:
        if "Service" not in block or "Node" not in block in "Checks" not in block:
            continue
        service = block["Service"]
        node = block["Node"]
        checks = block["Checks"]
        status = True
        if only_passing:
            for check in checks:
                status = status and (check.get('Status', 'unknown') == 'passing')
        for tag in tags:
            service_tags = service.get("Tags", [])
            if tag not in service_tags:
                status = False
        if not status:
            continue
        service_id = service.get('ID', None)
        try:
            container_name = service_id.split(':')[1]
            address = service['Address']
            port = service['Port']
        except:
            continue
        res.append({"service_name": service_name, "name": container_name, "ip": address, "port": port})
    fn = lambda x: "%s__%s__%i" % (x['name'], x['ip'], x['port'])
    return sorted(res, key=fn)

def consul_tuples(consul, services, only_passing=True, timeout=10, tags=[]):
    res = []
    for service_name in [x.split('::')[-1] for x in services]:
        res = res + _consul_tuples(consul, service_name, only_passing=only_passing, timeout=timeout, tags=tags)
    return res

if len(sys.argv) == 3:
    services = json.loads(sys.argv[2])
else:
    services = json.loads(os.environ['CONDRI_HAPROXY_SERVICES'])
tpls = consul_tuples(sys.argv[1], services)
print json.dumps(tpls, indent=4)
