#!/bin/bash

if test "${CONDRI_HAPROXY_PUBLISH_LINKS}" != "1"; then
    exit 0
fi

if ! test -f /etc/haproxy/haproxy.cfg; then
    exit 0
fi

# Deal with a lock
lockfile -1 -r 10 -l 60 /tmp/push_links.lock
if test $? -ne 0; then
    echo "WARNING: can't get lock after 10 seconds => exiting"
    exit 1
fi

cat >/tmp/link <<EOF
{
    "from": "${HOSTNAME}",
    "to": "[
EOF

FIRST=1
for TMP in `cat /etc/haproxy/haproxy.cfg |grep '^ *server' |awk '{print $3;}'`; do
    IP=`echo ${TMP} |awk -F ':' '{print $1;}'`
    PORT=`echo ${TMP} |awk -F ':' '{print $2;}'`
    if test ${FIRST} -eq 1; then
        FIRST=0
    else
        echo ", " >>/tmp/link
    fi
    cat >>/tmp/link <<EOF
{"ip": "${IP}", "port": ${PORT}}
EOF
done

cat >>/tmp/link <<EOF
    ],
    "datetime": "`date -u +"%Y-%m-%dT%H:%M:%SZ"`"
}
EOF
timeout 30 curl --data-binary "@/tmp/link" -XPUT "http://${CONDRI_HAPROXY_CONSUL}/v1/kv/published_links/${HOSTNAME}"
rm -f /tmp/push_links.lock
