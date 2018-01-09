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

from django.conf import settings
from django.core.cache import cache
from keystoneauth1.identity import v2 as keystone_v2
from keystoneauth1.identity import v3 as keystone_v3
from keystoneauth1 import session

from newton.pub.msapi import extsys

logger = logging.getLogger(__name__)


class VimDriverUtils(object):
    @staticmethod
    def get_vim_info(vimid):
        """
        Retrieve VIM information.

        :param vimid: VIM Identifier
        :return: VIM information
        """
        # TODO: get vim info from local cache firstly later from ESR
        return extsys.get_vim_by_id(vimid)

    @staticmethod
    def delete_vim_info(vimid):
        return extsys.delete_vim_by_id(vimid)

    @staticmethod
    def get_query_part(request):
        query = ""
        full_path = request.get_full_path()
        if '?' in full_path:
            _, query = full_path.split('?')
        return query

    @staticmethod
    def get_session(
            vim, tenant_id=None, tenant_name=None, auth_state=None):
        """
        get session object and optionally preload auth_state
        """
        auth = None

        params = {
            "auth_url": vim["url"],
            "username": vim["userName"],
            "password": vim["password"],
        }

        # tenantid takes precedence over tenantname
        if tenant_id:
            params["tenant_id"] = tenant_id
        else:
            # input tenant name takes precedence over the default one
            # from AAI data store
            params["tenant_name"] = (tenant_name if tenant_name
                                     else vim['tenant'])

        if '/v2' in params["auth_url"]:
            auth = keystone_v2.Password(**params)
        else:
            params["user_domain_name"] = vim["domain"]
            params["project_domain_name"] = vim["domain"]

            if 'tenant_id' in params:
                params["project_id"] = params.pop("tenant_id")
            if 'tenant_name' in params:
                params["project_name"] = params.pop("tenant_name")
            if '/v3' not in params["auth_url"]:
                params["auth_url"] = params["auth_url"] + "/v3",
            auth = keystone_v3.Password(**params)

        #preload auth_state which was acquired in last requests
        if auth_state:
           auth.set_auth_state(auth_state)

        return session.Session(auth=auth)

    @staticmethod
    def get_auth_state(session_obj):
        """
        Retrieve the authorization state
        :param session: OpenStack Session object
        :return: return a string dump of json object with token and
        resp_data of authentication request
        """
        auth = session_obj._auth_required(None, 'fetch a token')
        if auth:
            #trigger the authenticate request
            session_obj.get_auth_headers(auth)

            # norm_expires = utils.normalize_time(auth.expires)
            return auth.get_auth_state()

    @staticmethod
    def get_token_cache(token):
        """
        get auth_state and metadata fromm cache
        :param token:
        :return:
        """
        return cache.get(token), cache.get("meta_%s" % token)

    @staticmethod
    def update_token_cache(token, auth_state, metadata):
        """
        Stores into the cache the auth_state and metadata_catalog
        information.

        :param token: Base token to be used as an identifier
        :param auth_state: Authorization information
        :param metadata: Metadata Catalog information
        """
        if metadata and not cache.get(token):
            cache.set(
                token, auth_state, settings.CACHE_EXPIRATION_TIME)
            cache.set(
                "meta_%s" % token, metadata,
                settings.CACHE_EXPIRATION_TIME)

    @staticmethod
    def _replace_a_key(dict_obj, key_pair, reverse):
        old_key = key_pair[1] if reverse else key_pair[0]
        new_key = key_pair[0] if reverse else key_pair[1]

        old_value = dict_obj.pop(old_key, None)
        if old_value:
            dict_obj[new_key] = old_value

    @staticmethod
    def replace_key_by_mapping(dict_obj, mapping, reverse=False):
        for k in mapping:
            VimDriverUtils._replace_a_key(dict_obj, k, reverse)
