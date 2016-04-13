#!/bin/env python

import sys
import os
import json

services = json.loads(os.environ['CONDRI_HAPROXY_SERVICES'])
for x in [x.split('::')[-1] for x in services]:
    print x
