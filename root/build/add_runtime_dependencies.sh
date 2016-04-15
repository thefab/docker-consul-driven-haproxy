#!/bin/bash

mkdir -p /build

# note: procmail is required for lockfile command
yum --enablerepo=epel install -y haproxy procmail python-requests python-argparse
rpm -qa --qf '%{name}\n' >/build/original_packages.list
