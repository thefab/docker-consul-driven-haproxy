#!/bin/env python

import os
import sys
import uuid
import json
import argparse
import random

def _consul_services(consul, service_name, only_passing=True, timeout=10, tags=[], sort='alphabetic'):
    consul_cli = "timeout --signal=SIGKILL %i consul-cli --consul=%s" % (timeout, consul)
    random_id = str(uuid.uuid4())
    res = []
    try:
        return_code = os.system("%s health service %s >/tmp/%s 2>/dev/null" % (consul_cli, service_name, random_id))
        if return_code != 0:
            raise Exception("exception during consul request")
        with open("/tmp/%s" % random_id, "r") as f:
            content = json.loads(f.read())
        os.unlink("/tmp/%s" % random_id)
    except:
        os.unlink("/tmp/%s" % random_id)
        raise Exception("exception during consul request")
    for block in content:
        if "Service" not in block or "Node" not in block in "Checks" not in block:
            continue
        service = block["Service"]
        node = block["Node"]
        checks = block["Checks"]
        status = "passing"
        service_tags = service.get("Tags", [])
        service_id = service.get('ID', None)
        for check in checks:
            if check.get('Status', 'unknown') != 'passing':
                status = 'not_passing'
                break
        if only_passing and status != "passing":
            continue
        tags_found = True
        for tag in tags:
            if len(tag) >0 and tag not in service_tags:
                tags_found = False
                break
        if not(tags_found):
            continue
        try:
            container_name = service_id.split(':')[1]
            address = service['Address']
            port = service['Port']
        except:
            continue
        res.append({"service_name": service_name, "name": container_name, "ip": address, "port": port, "status": status, "tags": service_tags})
    if sort == 'alphabetic':
        fn = lambda x: "%s__%s__%i" % (x['name'], x['ip'], x['port'])
        return sorted(res, key=fn)
    else:
        # random sort
        random.shuffle(res)
        return res

def consul_services(consul, service_names, only_passing=True, timeout=10, tags=[], sort='alphabetic', limit_to=None):
    res = []
    number_of_services_by_container = {}
    for service_name in service_names: 
        tmp = _consul_services(consul, service_name, only_passing=only_passing, timeout=timeout, tags=tags, sort=sort)
        res = res + tmp
        for item in tmp:
            key = item['name'] + "@" + item['ip']
            if key in number_of_services_by_container:
                number_of_services_by_container[key] = number_of_services_by_container[key] + 1
            else:
                number_of_services_by_container[key] = 1
    if limit_to is not None:
        selected_keys = []
        if sort == 'alphabetic':
            keys = sorted(number_of_services_by_container.keys())
        else:
            # random sort
            keys = number_of_services_by_container.keys()
            random.shuffle(keys)
        for key in keys:
            if number_of_services_by_container[key] == len(service_names):
                selected_keys.append(key)
                if limit_to == 'one':
                    break
        new_res = []
        for selected_key in selected_keys: 
            new_res = new_res + [x for x in res if x['name'] == selected_key.split('@')[0] and x['ip'] == selected_key.split('@')[1]]
        return new_res
    else:  
        return res

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Request a consul server to get a healthy service list')
    parser.add_argument('--consul', help="consul server host:port", default="localhost:8085")
    parser.add_argument('--consul-timeout', help="timeout for consult request", default=10, type=int)
    parser.add_argument('--all-states', help="if set, return all services and not only healthy ones", action="store_true")
    parser.add_argument('--tags', help="coma separated of tags to find in services", default="")
    parser.add_argument('--sort', help="if 'alphabetic', for a given service, sort reply in alphabetic order (default) ; if 'random', sort in random order", default="alphabetic", choices=('alphabetic', 'random'))
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--limit-to-one-container', help="limit replies to a single container which has to support all specified services", action="store_true")
    group.add_argument('--limit-to-full-featured-containers', help="limit replies to containers which support all specified services", action="store_true")
    parser.add_argument("service_names", help="consul service names (separated by ',')")
    args = parser.parse_args()
   
    limit_to = None
    if args.limit_to_one_container:
        limit_to = "one"
    elif args.limit_to_full_featured_containers:
        limit_to = "full"
    tpls = consul_services(args.consul, args.service_names.split(','),
                           only_passing=not(args.all_states), timeout=args.consul_timeout, tags=args.tags.split(','),
                           sort=args.sort, limit_to=limit_to)
    print json.dumps(tpls, indent=4)
