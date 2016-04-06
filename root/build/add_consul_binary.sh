#!/bin/bash

ARCH=linux_amd64
BUILD_DIR=/build
DEST_DIR=/usr/local/bin

mkdir -p ${BUILD_DIR}
mkdir -p ${DEST_DIR}

VERSION=0.6.4
NAME=consul
ARCHIVE_NAME=${NAME}_${VERSION}_${ARCH}.zip
ARCHIVE_URL=https://releases.hashicorp.com/${NAME}/${VERSION}/${ARCHIVE_NAME}

cd ${BUILD_DIR} || exit 1
wget -O ${ARCHIVE_NAME} ${ARCHIVE_URL}
unzip ${ARCHIVE_NAME}
mv ${NAME} ${DEST_DIR}
