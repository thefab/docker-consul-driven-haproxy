#!/bin/bash

mkdir -p /build
yum --enablerepo=epel install -y haproxy wget unzip
rpm -qa --qf '%{name}\n' >/build/original_packages.list
