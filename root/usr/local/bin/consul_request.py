#!/bin/env python

import os
import sys
import uuid
import json
import argparse
import random


def _id_to_container_name_fn(service_id):
    tmp = service_id.split(':')
    if len(tmp) == 3 or len(tmp) == 4:
        return tmp[1]
    else:
        return service_id


def consul_kv(consul, path, timeout=10):
    random_id = str(uuid.uuid4())
    consul_cmd = "timeout --signal=SIGKILL %i consul-cli --consul=%s kv read %s >/tmp/%s 2>/dev/null" % (timeout, consul, path, random_id)
    try:
        return_code = os.system(consul_cmd)
        if return_code != 0:
            raise Exception("exception during consul request")
        with open("/tmp/%s" % random_id, "r") as f:
            content = f.read().strip()
        os.unlink("/tmp/%s" % random_id)
        if len(content) == 0:
            return None
        return content
    except:
        os.unlink("/tmp/%s" % random_id)
        raise Exception("exception during consul request")


def _consul_services(consul, service_name, only_passing=True, timeout=10, tags=[], sort='alphabetic', id_to_container_name_fn=_id_to_container_name_fn, limit_by_container_name=None):
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
        if limit_by_container_name is not None and container_name != limit_by_container_name:
            continue
        res.append({"service_name": service_name, "name": container_name, "ip": address, "port": port, "status": status, "tags": service_tags})
    if sort == 'alphabetic':
        fn = lambda x: "%s__%s__%i" % (x['name'], x['ip'], x['port'])
        return sorted(res, key=fn)
    else:
        # random sort
        random.shuffle(res)
        return res

def consul_services(consul, service_names, only_passing=True, timeout=10, tags=[], sort='alphabetic', limit_to=None, id_to_container_name_fn=_id_to_container_name_fn, limit_by_container_name=None):
    res = []
    number_of_services_by_container = {}
    for service_name in service_names: 
        tmp = _consul_services(consul, service_name, only_passing=only_passing, timeout=timeout, tags=tags, sort=sort, id_to_container_name_fn=id_to_container_name_fn, limit_by_container_name=limit_by_container_name)
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
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('--limit-to-one-container', help="limit replies to a single container which has to support all specified services", action="store_true")
    group1.add_argument('--limit-to-full-featured-containers', help="limit replies to containers which support all specified services", action="store_true")
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('--limit-by-container-name', help="just considerer this container name", default=None)
    group2.add_argument('--limit-by-container-name-at', help="just considerer the container name found in consul kv at the given path", default=None)
    parser.add_argument("service_names", help="consul service names (separated by ',')")
    args = parser.parse_args()
   
    limit_to = None
    if args.limit_to_one_container:
        limit_to = "one"
    elif args.limit_to_full_featured_containers:
        limit_to = "full"
    limit_by_container_name = None
    if args.limit_by_container_name_at is not None:
        limit_by_container_name = consul_kv(args.consul, args.limit_by_container_name_at)
    tpls = consul_services(args.consul, args.service_names.split(','),
                           only_passing=not(args.all_states), timeout=args.consul_timeout, tags=args.tags.split(','),
                           sort=args.sort, limit_to=limit_to, limit_by_container_name=limit_by_container_name)
    print json.dumps(tpls, indent=4)
