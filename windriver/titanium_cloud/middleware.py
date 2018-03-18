# Copyright (c) 2017-2018 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid
from django.conf import settings
from onaplogging.mdcContext import MDC

FORWARDED_FOR_FIELDS = ["HTTP_X_FORWARDED_FOR", "HTTP_X_FORWARDED_HOST",
                        "HTTP_X_FORWARDED_SERVER"]

class LogContextMiddleware(object):

    #  the last IP behind multiple proxies,  if no exist proxies
    #  get local host ip.
    def _getLastIp(self, request):

        ip = ""
        try:
            for field in FORWARDED_FOR_FIELDS:
                if field in request.META:
                    if ',' in request.META[field]:
                        parts = request.META[field].split(',')
                        ip = parts[-1].strip().split(":")[0]
                    else:
                        ip = request.META[field].split(":")[0]

            if ip == "":
                ip = request.META.get("HTTP_HOST").split(":")[0]

        except Exception:
            pass

        return ip


    def process_request(self, request):
        # fetch propageted Id from other component. if do not fetch id,
        # generate one.
        ReqeustID = request.META.get("HTTP_X_TRANSACTIONID", None)
        if ReqeustID is None:
            ReqeustID = uuid.uuid3(uuid.NAMESPACE_URL, settings.MULTIVIM_VERSION)
        MDC.put("requestID", ReqeustID)
        # generate the reqeust id
        InvocationID = uuid.uuid3(uuid.NAMESPACE_DNS, settings.MULTIVIM_VERSION)
        MDC.put("invocationID", InvocationID)
        MDC.put("serviceName", settings.MULTIVIM_VERSION)
        MDC.put("serviceIP", self._getLastIp(request))
        return None

    def process_response(self, request, response):

        MDC.clear()
        return response

