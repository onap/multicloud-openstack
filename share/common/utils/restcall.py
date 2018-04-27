# Copyright (c) 2017-2018 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import six
import base64

import codecs
import json
import traceback
import sys

import logging
from six.moves import urllib
import httplib2
import uuid

from rest_framework import status
from django.conf import settings

rest_no_auth, rest_oneway_auth, rest_bothway_auth = 0, 1, 2
HTTP_200_OK, HTTP_201_CREATED = '200', '201'
HTTP_204_NO_CONTENT, HTTP_202_ACCEPTED = '204', '202'
status_ok_list = [HTTP_200_OK, HTTP_201_CREATED,
                  HTTP_204_NO_CONTENT, HTTP_202_ACCEPTED]
HTTP_404_NOTFOUND, HTTP_403_FORBIDDEN = '404', '403'
HTTP_401_UNAUTHORIZED, HTTP_400_BADREQUEST = '401', '400'

MAX_RETRY_TIME = 3

logger = logging.getLogger(__name__)


def _call_req(base_url, user, passwd, auth_type,
             resource, method, extra_headers='', content=''):
    callid = str(uuid.uuid1())
    ret = None
    resp_status = None
    try:
        full_url = _combine_url(base_url, resource)
        headers = {
            'content-type': 'application/json',
            'accept': 'application/json'
        }

        if extra_headers:
            headers.update(extra_headers)
#        if user:
#            headers['Authorization'] = \
#                'Basic ' + str(codecs.encode('%s:%s' % (user, passwd), "ascii"))

        if user:
            tmpauthsource = '%s:%s' % (user, passwd)
            if six.PY3:
                tmpauthsource = tmpauthsource.encode('utf-8')
            headers['Authorization'] = 'Basic ' + \
                base64.b64encode(tmpauthsource).decode('utf-8')

        logger.info("Making rest call ... ")
        logger.debug("uri,method, header = %s, %s, %s" % (full_url, method.upper(), headers))
        if content:
            logger.debug("content = %s" % (content))

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
                    resp['status'], codecs.decode(
                        resp_content, 'UTF-8')
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
        logger.info("Rest call finished with status = %s", resp_status)
        logger.debug("with response content = %s" % resp_body)
    except urllib.error.URLError as err:
        logger.error("status=%s, error message=%s" % (resp_status, str(err)))
        ret = [2, str(err), resp_status]
    except Exception:
        logger.error(traceback.format_exc())
        logger.error("[%s]ret=%s" % (callid, str(sys.exc_info())))
        if not resp_status:
            resp_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        ret = [3, str(sys.exc_info()), resp_status]
    except:
        logger.error(traceback.format_exc())
        if not resp_status:
            resp_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        ret = [4, str(sys.exc_info()), resp_status]

    return ret


def req_by_msb(resource, method, content=''):
    base_url = "http://%s:%s/" % (settings.MSB_SERVICE_ADDR, settings.MSB_SERVICE_PORT)
    return _call_req(base_url, "", "", rest_no_auth,
                    resource, method, "", content)


def req_to_vim(base_url, resource, method, extra_headers='', content=''):
    return _call_req(base_url, "", "", rest_no_auth,
                    resource, method, extra_headers, content)


def req_to_aai(resource, method, content='', appid=settings.MULTICLOUD_APP_ID):
    tmp_trasaction_id = '9003' #str(uuid.uuid1())
    headers = {
        'X-FromAppId': appid,
        'X-TransactionId': tmp_trasaction_id,
        'content-type': 'application/json',
        'accept': 'application/json'
    }

    return _call_req(settings.AAI_BASE_URL, settings.AAI_USERNAME, settings.AAI_PASSWORD, rest_no_auth,
                    resource, method, content=json.dumps(content), extra_headers=headers)


def _combine_url(base_url, resource):
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
