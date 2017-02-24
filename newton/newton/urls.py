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

from django.conf.urls import include, url
from newton.pub.config.config \
    import REG_TO_MSB_WHEN_START, REG_TO_MSB_REG_URL, REG_TO_MSB_REG_PARAM

urlpatterns = [
    url(r'^', include('newton.swagger.urls')),
    url(r'^', include('newton.samples.urls')),
    url(r'^openoapi/multivim-newton/v1/(?P<vimid>[0-9a-zA-Z_-]+)/'
        '(?P<tenantid>[0-9a-zA-Z_-]+)/', include('newton.requests.urls')),
]

# regist to MSB when startup
if REG_TO_MSB_WHEN_START:
    import json
    from newton.pub.utils.restcall import req_by_msb
    req_by_msb(REG_TO_MSB_REG_URL, "POST",
               json.JSONEncoder().encode(REG_TO_MSB_REG_PARAM))
