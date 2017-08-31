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

import sys
import traceback
import logging
from six.moves import urllib
import uuid
import http.client as httplib
import httplib2

from rest_framework import status

from newton.pub.config.config import MSB_SERVICE_IP, MSB_SERVICE_PORT

rest_no_auth, rest_oneway_auth, rest_bothway_auth = 0, 1, 2
HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_202_ACCEPTED \
    = '200', '201', '204', '202'
status_ok_list \
    = [HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_202_ACCEPTED]
HTTP_404_NOTFOUND, HTTP_403_FORBIDDEN, \
    HTTP_401_UNAUTHORIZED, HTTP_400_BADREQUEST = '404', '403', '401', '400'
MAX_RETRY_TIME = 3

logger = logging.getLogger(__name__)


def call_req(base_url, user, passwd, auth_type,
             resource, method, extra_headers='', content=''):
    callid = str(uuid.uuid1())
#    logger.debug("[%s]call_req('%s','%s','%s',%s,'%s','%s','%s')" % (
#        callid, base_url, user, passwd, auth_type, resource, method, content))
    ret = None
    resp_status = None
    try:
        full_url = combine_url(base_url, resource)
        headers = {
            'content-type': 'application/json',
            'accept': 'application/json'
        }

        if extra_headers:
            headers.update(extra_headers)
        if user:
            headers['Authorization'] = \
                'Basic ' + ('%s:%s' % (user, passwd)).encode("base64")
        ca_certs = None
        for retry_times in range(MAX_RETRY_TIME):
            http = httplib2.Http(
                ca_certs=ca_certs,
                disable_ssl_certificate_validation=(auth_type == rest_no_auth))
            http.follow_all_redirects = True
            try:
                resp, resp_content = http.request(full_url,
                                                  method=method.upper(),
                                                  body=content,
                                                  headers=headers)
                resp_status, resp_body = \
                    resp['status'], resp_content.decode('UTF-8')
#                logger.debug("[%s][%d]status=%s,resp_body=%s)" %
#                             (callid, retry_times, resp_status, resp_body))
                if resp_status in status_ok_list:
                    ret = [0, resp_body, resp_status]
                else:
                    ret = [1, resp_body, resp_status]
                break
            except httplib.ResponseNotReady:
#                logger.debug("retry_times=%d", retry_times)
                ret = [1, "Unable to connect to %s" % full_url, resp_status]
                continue
    except urllib2.URLError as err:
        ret = [2, str(err), resp_status]
    except Exception:
        logger.error(traceback.format_exc())
        logger.error("[%s]ret=%s" % (callid, str(sys.exc_info())))
        if not resp_status:
            resp_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        ret = [3, str(sys.exc_info()), resp_status]

#    logger.debug("[%s]ret=%s" % (callid, str(ret)))
    return ret


def req_by_msb(resource, method, content=''):
    base_url = "http://%s:%s/" % (MSB_SERVICE_IP, MSB_SERVICE_PORT)
#    logger.debug("requests--get::> %s" % "33")
    return call_req(base_url, "", "", rest_no_auth,
                    resource, method, "", content)


def req_to_vim(base_url, resource, method, extra_headers='', content=''):
    return call_req(base_url, "", "", rest_no_auth,
                    resource, method, extra_headers, content)


def combine_url(base_url, resource):
    full_url = None

    if not resource:
        return base_url

    if base_url.endswith('/') and resource.startswith('/'):
        full_url = base_url[:-1] + resource
    elif base_url.endswith('/') and not resource.startswith('/'):
        full_url = base_url + resource
    elif not base_url.endswith('/') and resource.startswith('/'):
        full_url = base_url + resource
    else:
        full_url = base_url + '/' + resource
    return full_url
