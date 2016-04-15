#!/bin/env python

import sys
import os

services = os.environ['CONDRI_HAPROXY_SERVICES'].split(',')
for x in [x.split('::')[-1] for x in services]:
    print x
