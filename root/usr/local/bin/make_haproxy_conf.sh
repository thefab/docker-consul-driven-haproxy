#!/bin/bash

lockfile -1 -r 10 -l 60 /tmp/make_haproxy_conf.lock
if test $? -ne 0; then
    exit 0
fi

OLD_CONF=`cat /etc/haproxy/haproxy.cfg.md5 2>/dev/null`
export CONDRI_HAPROXY_SERVERS="`consul_request.py ${CONDRI_HAPROXY_CONSUL} ${CONDRI_HAPROXY_SERVICE_NAME}`"

cat /etc/haproxy/haproxy.cfg.template |envtpl --allow-missing >/etc/haproxy/haproxy.cfg.tmp
# FIXME: validate conf
mv -f /etc/haproxy/haproxy.cfg.tmp /etc/haproxy/haproxy.cfg
cat /etc/haproxy/haproxy.cfg |md5sum |awk '{print $1;}' >/etc/haproxy/haproxy.cfg.md5

NEW_CONF=`cat /etc/haproxy/haproxy.cfg.md5 2>/dev/null`
if test "${NEW_CONF}" != "${OLD_CONF}"; then
    if test "${1}" = "RELOAD"; then
        echo "conf changed, reloading haproxy..."
        /etc/init.d/haproxy reload >/dev/null 2>&1
    fi
fi

rm -f /tmp/make_haproxy_conf.lock
