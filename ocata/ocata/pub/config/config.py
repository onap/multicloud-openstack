# Copyright (c) 2017 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import os

# [MSB]
MSB_SERVICE_IP = '127.0.0.1'
MSB_SERVICE_PORT = '80'

#[Multicloud]
MULTICLOUD_PREFIX = "http://%s:%s/api/multicloud-ocata/v0" %(MSB_SERVICE_IP, MSB_SERVICE_PORT)

# [A&AI]
AAI_ADDR = "aai.api.simpledemo.openecomp.org"
AAI_PORT = "8443"
AAI_SERVICE_URL = 'https://%s:%s/aai' % (AAI_ADDR, AAI_PORT)
AAI_SCHEMA_VERSION = "v11"
AAI_USERNAME = 'AAI'
AAI_PASSWORD = 'AAI'

AAI_BASE_URL = "%s/%s" % (AAI_SERVICE_URL, AAI_SCHEMA_VERSION)

MULTICLOUD_APP_ID = 'MultiCloud-Ocata'

# [IMAGE LOCAL PATH]
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
