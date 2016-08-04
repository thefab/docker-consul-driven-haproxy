#!/bin/bash

# Deal with a lock
lockfile -1 -r 10 -l 60 /tmp/make_haproxy_conf.lock
if test $? -ne 0; then
    echo "WARNING: can't get lock after 10 seconds => exiting"
    exit 1
fi

# Get the old conf md5
OLD_CONF=`cat /etc/haproxy/haproxy.cfg.md5 2>/dev/null`

# Request consul about backend servers to use
CONSUL_SERVICE_NAMES=`get_service_names.py |xargs |sed 's/ /,/g'`
OPTIONS=""
if test "${CONDRI_HAPROXY_LIMIT_TO_ONE_CONTAINER}" = "1"; then
  OPTIONS="${OPTIONS} --limit-to-one-container"
elif test "${CONDRI_HAPROXY_LIMIT_TO_FULL_FEATURED_CONTAINERS}" = "1"; then
  OPTIONS="${OPTIONS} --limit-to-full-featured-containers"
fi
if test "${CONDRI_HAPROXY_LIMIT_BY_CONTAINER_NAME}" != ""; then
  OPTIONS="${OPTIONS} --limit-by-container-name=${CONDRI_HAPROXY_LIMIT_BY_CONTAINER_NAME}"
elif test "${CONDRI_HAPROXY_LIMIT_BY_CONTAINER_NAME_AT}" != ""; then
  OPTIONS="${OPTIONS} --limit-by-container-name-at=${CONDRI_HAPROXY_LIMIT_BY_CONTAINER_NAME_AT}"
fi
export CONDRI_HAPROXY_SERVERS="`consul_request.py ${OPTIONS} --tags=${CONDRI_HAPROXY_SERVICE_TAGS} --consul=${CONDRI_HAPROXY_CONSUL} ${CONSUL_SERVICE_NAMES}`"
if test "${CONDRI_HAPROXY_SERVERS}" = ""; then
    echo "ERROR: can't get a reply from consul"
    rm -f /tmp/make_haproxy_conf.lock
    exit 1
fi
N=`echo "{{ CONDRI_HAPROXY_SERVERS |from_json |length }}" |envtpl --allow-missing`
if test ${N} -eq 0; then
    # empty result
    if test "${CONDRI_HAPROXY_IGNORE_EMPTY_CONSUL_RESULTS_MINUTES}" != "0"; then
        if test -f /etc/haproxy/haproxy.cfg.md5; then
            # We have a valid configuration file
            N=`find /etc/haproxy/haproxy.cfg.md5 -mmin +${CONDRI_HAPROXY_IGNORE_EMPTY_CONSUL_RESULTS_MINUTES} 2>/dev/null |wc -l`
            if test ${N} -eq 0; then
                # The file is more recent than CONDRI_HAPROXY_IGNORE_EMPTY_CONSUL_RESULTS_MINUTES value
                echo "WARNING: empty result from consul but CONDRI_HAPROXY_IGNORE_EMPTY_CONSUL_RESULTS_MINUTES is set"
                echo "we keep the old configuration file"
                rm -f /tmp/make_haproxy_conf.lock
                exit 0
            fi
        fi
    fi
fi

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
if test "${1}" = "RELOAD"; then
    if test "${NEW_CONF}" != "${OLD_CONF}"; then
        echo
        echo `date`": conf changed, new conf:"
        echo "================================================================"
        cat /etc/haproxy/haproxy.cfg |grep '[a-zA-Z]'
        echo "================================================================"
        echo "Reloading haproxy..."
        /etc/init.d/haproxy reload >/dev/null 2>&1
        push_links.sh
    fi
else
    echo
    echo `date`": conf changed, new conf:"
    echo "================================================================"
    cat /etc/haproxy/haproxy.cfg |grep '[a-zA-Z]'
    echo "================================================================"
    push_links.sh
fi

# Removing the lock
rm -f /tmp/make_haproxy_conf.lock
