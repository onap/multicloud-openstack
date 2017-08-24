# Copyright (c) 2017 Wind River Systems, Inc.
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
import logging

import datetime

from django.core.cache import cache

from keystoneauth1 import _utils as utils
from keystoneauth1.identity import v2 as keystone_v2
from keystoneauth1.identity import v3 as keystone_v3
from keystoneauth1 import session

from newton.pub.msapi.extsys import get_vim_by_id

logger = logging.getLogger(__name__)


class VimDriverUtils(object):
    @staticmethod
    def get_vim_info(vimid):
        # get vim info from local cache firstly
        # if cache miss, get it from ESR service
        vim = get_vim_by_id(vimid)
        return vim

    @staticmethod
    def get_query_part(request):
        query = ""
        full_path = request.get_full_path()
        if '?' in full_path:
            _, query = request.get_full_path().split('?')
        return query

    @staticmethod
    def get_session(vim, tenantid=None, auth_state=None):
        """
        get session object and optionally preload auth_state
        """
        auth = None
        if '/v2' in vim["url"]:
            auth = keystone_v2.Password(auth_url=vim["url"],
                                        username=vim["userName"],
                                        password=vim["password"],
                                        tenant_name=vim["tenant"])
        elif '/v3' in vim["url"]:
            auth = keystone_v3.Password(auth_url=vim["url"],
                                        username=vim["userName"],
                                        password=vim["password"],
                                        project_name=vim["tenant"],
                                        user_domain_id='default',
                                        project_domain_id='default')

        #preload auth_state which was acquired in last requests
        if auth_state:
           auth.set_auth_state(auth_state)

        return session.Session(auth=auth)


    @staticmethod
    def get_auth_state(vim, session):
        auth = session._auth_required(None, 'fetch a token')
        if not auth:
            return None

        #trigger the authenticate request
        session.get_auth_headers(auth)

#        norm_expires = utils.normalize_time(auth.expires)

        #return a string dump of json object with token and resp_data of authentication request
        return auth.get_auth_state()
#        return auth.get_auth_ref(session)

    @staticmethod
    def update_token_cache(vim, session, old_token, auth_state):

        tmp_auth_token = session.get_token()
        #check if need to update token:auth_state mapping
        if tmp_auth_token != old_token:
            tmp_auth_state = cache.delete(old_token)

        # store the auth_state, memcached
        # set expiring in 1 hour
        cache.set(tmp_auth_token, auth_state, 3600)

        #return new token
        return tmp_auth_token

    @staticmethod
    def replace_a_key(dict_obj, keypair, reverse=False):
        old_key, new_key = None, None
        if reverse:
            old_key, new_key = keypair[1], keypair[0]
        else:
            old_key, new_key = keypair[0], keypair[1]

        v = dict_obj.pop(old_key, None)
        if v:
            dict_obj[new_key] = v

    @staticmethod
    def replace_key_by_mapping(dict_obj, mapping, reverse=False):
        for k in mapping:
            VimDriverUtils.replace_a_key(dict_obj, k, reverse)
