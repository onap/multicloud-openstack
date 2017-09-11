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
import json
import traceback
import logging
from six.moves import urllib
import uuid
from six.moves import http_client
import httplib2
import uuid

from rest_framework import status
from newton.pub.config import config

rest_no_auth, rest_oneway_auth, rest_bothway_auth = 0, 1, 2

status_ok_list \
    = [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_204_NO_CONTENT, status.HTTP_202_ACCEPTED]

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
            except Exception as ex:
                if 'httplib.ResponseNotReady' in str(sys.exc_info()):
                    logger.debug("retry_times=%d", retry_times)
                    logger.error(traceback.format_exc())
                    ret = [1, "Unable to connect to %s" % full_url, resp_status]
                    continue
                raise ex
    except urllib.error.URLError as err:
        ret = [2, str(err), resp_status]
    except Exception as ex:
        logger.error(traceback.format_exc())
        logger.error("[%s]ret=%s" % (callid, str(sys.exc_info())))
        if not resp_status:
            resp_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        ret = [3, str(sys.exc_info()), resp_status]
    except:
        logger.error(traceback.format_exc())
        ret = [4, str(sys.exc_info()), resp_status]

#    logger.debug("[%s]ret=%s" % (callid, str(ret)))
    return ret


def req_by_msb(resource, method, content=''):
    base_url = "http://%s:%s/" % (config.MSB_SERVICE_ADDR, config.MSB_SERVICE_PORT)
#    logger.debug("requests--get::> %s" % "33")
    return call_req(base_url, "", "", rest_no_auth,
                    resource, method, "", content)


def req_to_vim(base_url, resource, method, extra_headers='', content=''):
    return call_req(base_url, "", "", rest_no_auth,
                    resource, method, extra_headers, content)

def req_to_aai(resource, method, content='', appid=config.MULTICLOUD_APP_ID):
    tmp_trasaction_id = str(uuid.uuid1())
    headers = {
        'X-FromAppId': appid,
        'X-TransactionId': tmp_trasaction_id,
        'content-type': 'application/json',
        'accept': 'application/json'
    }

    logger.debug("req_to_aai--%s::> %s, %s" % (tmp_trasaction_id, method, resource))
    return call_req(config.AAI_BASE_URL, config.AAI_USERNAME, config.AAI_PASSWORD, rest_no_auth,
                    resource, method, content=json.dumps(content), extra_headers=headers)


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
