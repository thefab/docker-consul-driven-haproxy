#!/bin/bash

timeout -s KILL 300 consul watch -http-addr=${CONDRI_HAPROXY_CONSUL} -type=service -passingonly=true -service=${CONDRI_HAPROXY_SERVICE_NAME} make_haproxy_conf.sh RELOAD
make_haproxy_conf.sh RELOAD
