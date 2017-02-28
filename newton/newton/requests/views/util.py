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
    def get_session(vim, tenantid=None):
        """
        get vim info from ESR and create auth plugin and session object
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
        return session.Session(auth=auth)

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
            VimDriverUtils.replace_a_key(dict_obj, k)
