#!/bin/bash

if test "${CONDRI_HAPROXY_PUBLISH_LINKS}" != "1"; then
    exit 0
fi

curl -XDELETE "http://${CONDRI_HAPROXY_CONSUL}/v1/kv/published_links/${HOSTNAME}"
