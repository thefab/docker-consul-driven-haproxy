#!/bin/bash

# Deal with a lock
lockfile -1 -r 10 -l 60 /tmp/make_haproxy_conf.lock
if test $? -ne 0; then
    exit 1
fi

# Get the old conf md5
OLD_CONF=`cat /etc/haproxy/haproxy.cfg.md5 2>/dev/null`

# Request consul about backend servers to use
export CONDRI_HAPROXY_SERVERS="`consul_request.py ${CONDRI_HAPROXY_CONSUL}`"

# Make new configuration file
cat /etc/haproxy/haproxy.cfg.template |envtpl --allow-missing >/etc/haproxy/haproxy.cfg.tmp

# Test this new configuration file
haproxy -c -f /etc/haproxy/haproxy.cfg.tmp >/dev/null 2>&1
if test $? -ne 0; then
    echo "ERROR: bad configuration file generated for haproxy, ignoring it"
    rm -f /tmp/make_haproxy_conf.lock
    exit 1
fi

# Install the new configuration file
mv -f /etc/haproxy/haproxy.cfg.tmp /etc/haproxy/haproxy.cfg
cat /etc/haproxy/haproxy.cfg |md5sum |awk '{print $1;}' >/etc/haproxy/haproxy.cfg.md5

# If RELOAD is passed as first argument of the script
# Reload haproxy if necessary
NEW_CONF=`cat /etc/haproxy/haproxy.cfg.md5 2>/dev/null`
if test "${NEW_CONF}" != "${OLD_CONF}"; then
    if test "${1}" = "RELOAD"; then
        echo "conf changed, reloading haproxy..."
        /etc/init.d/haproxy reload >/dev/null 2>&1
    fi
fi

# Removing the lock
rm -f /tmp/make_haproxy_conf.lock
