#!/bin/bash

export CONDRI_HAPROXY_SERVERS="`consul_request.py ${CONDRI_HAPROXY_CONSUL} ${CONDRI_HAPROXY_SERVICE_NAME}`"
cat /etc/haproxy/haproxy.cfg.template |envtpl --allow-missing >/etc/haproxy/haproxy.cfg
cat /etc/haproxy/haproxy.cfg |md5sum |awk '{print $1;}' >/etc/haproxy/haproxy.cfg.md5
