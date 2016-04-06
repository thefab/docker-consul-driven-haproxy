#!/bin/bash

ARCH=linux_amd64
BUILD_DIR=/build
DEST_DIR=/usr/local/bin

mkdir -p ${BUILD_DIR}
mkdir -p ${DEST_DIR}

VERSION=0.2.0
NAME=consul-cli
ARCHIVE_NAME=${NAME}_${VERSION}_${ARCH}.tar.gz
ARCHIVE_URL=https://github.com/CiscoCloud/${NAME}/releases/download/v${VERSION}/${ARCHIVE_NAME}

cd ${BUILD_DIR} || exit 1
wget -O ${ARCHIVE_NAME} ${ARCHIVE_URL}
zcat ${ARCHIVE_NAME} |tar xvf -
mv ${NAME}_${VERSION}_${ARCH}/${NAME} ${DEST_DIR}
