# Copyright (c) 2018 Intel Corporation, Inc.
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

from django.core.cache import cache
import mock
import unittest

from newton_base import util
from newton_base.tests import mock_info


class TestUtil(unittest.TestCase):

    def test_get_query(self):
        query_string = "name=ferret&color=purple"
        mock_request = mock.Mock()
        mock_request.get_full_path.side_effect = [
            "path/to/page?" + query_string,
            "path/to/page"
        ]

        self.assertEqual(
            query_string, util.VimDriverUtils.get_query_part(
                mock_request))
        self.assertEqual(
            "", util.VimDriverUtils.get_query_part( mock_request))

    def test_get_new_openstack_v2_session_with_tenant_id(self):
        vim_info = mock_info.MOCK_VIM_INFO.copy()
        vim_info["url"] = "http://128.224.180.14:5000/v2"
        tenant_it = "1a62b3971d774404a504c5d9a3e506e3"

        os_session = util.VimDriverUtils.get_session(
            vim_info, tenant_it)

        self.assertIsNotNone(os_session)
        self.assertIsNotNone(os_session.auth)
        self.assertEqual(vim_info["url"], os_session.auth.auth_url)
        self.assertEqual(vim_info["userName"],
                         os_session.auth.username)
        self.assertEqual(vim_info["password"],
                         os_session.auth.password)

    def test_get_new_openstack_v3_session_with_project_id(self):
        projectid = "1a62b3971d774404a504c5d9a3e506e3"
        os_session = util.VimDriverUtils.get_session(
            mock_info.MOCK_VIM_INFO, projectid)

        self.assertIsNotNone(os_session)
        self.assertIsNotNone(os_session.auth)
        self.assertEqual(mock_info.MOCK_VIM_INFO["url"],
                         os_session.auth.auth_url)
        self.assertEqual(mock_info.MOCK_VIM_INFO["domain"],
                         os_session.auth.project_domain_name)
        self.assertEqual(projectid,
                         os_session.auth.project_id)

    def test_get_new_openstack_session_with_project_id(self):
        vim_info = mock_info.MOCK_VIM_INFO.copy()
        vim_info["url"] = "http://128.224.180.14:5000"
        project_id = "1a62b3971d774404a504c5d9a3e506e3"

        os_session = util.VimDriverUtils.get_session(
            vim_info, project_id)

        self.assertIsNotNone(os_session)
        self.assertIsNotNone(os_session.auth)
        self.assertEqual(vim_info["url"] + "/v3",
                         os_session.auth.auth_url[0])

    def test_get_new_openstack_v3_session_with_project_name(self):
        project_name = "demo"
        os_session = util.VimDriverUtils.get_session(
            mock_info.MOCK_VIM_INFO, tenant_name=project_name)

        self.assertIsNotNone(os_session)
        self.assertIsNotNone(os_session.auth)
        self.assertEqual(project_name,
                         os_session.auth.project_name)

    def test_get_auth_state_from_valid_session(self):
        test_result = "auth_state"

        mock_auth = mock.Mock()
        mock_auth.get_auth_state.return_value = test_result
        mock_session = mock.Mock()
        mock_session._auth_required.return_value = mock_auth

        auth_state = util.VimDriverUtils.get_auth_state(mock_session)

        self.assertIsNotNone(auth_state)
        self.assertEqual(test_result, auth_state)

    def test_get_auth_state_from_invalid_session(self):
        mock_session = mock.Mock()
        mock_session._auth_required.return_value = None

        self.assertIsNone(util.VimDriverUtils.get_auth_state(
            mock_session))

    @mock.patch.object(cache, 'get')
    def test_get_valid_tokens_from_cache(self, mock_cache_get):
        mock_cache_get.return_value = "valid_token"

        token, meta_token = util.VimDriverUtils.get_token_cache(
            "token")
        self.assertIsNotNone(token)
        self.assertIsNotNone(meta_token)

    @mock.patch.object(cache, 'get')
    def test_update_cache_expired_info(self, mock_cache_get):
        mock_cache_get.return_value = None

        util.VimDriverUtils.update_token_cache(
            "token", "auth_state", "metadata")

    @mock.patch.object(cache, 'get')
    def test_update_cache_info(self, mock_cache_get):
        mock_cache_get.return_value = "existing"

        util.VimDriverUtils.update_token_cache(
            "token", "auth_state", "metadata")

    def test_replace_keys_of_dict(self):
        dict_obj = {
            "project_id": "demo",
            "ram": "16G"
        }
        new_keys = ["tenantId", "memory"]
        mapping = [(o, n) for o, n in zip(dict_obj.keys(), new_keys)]
        util.VimDriverUtils.replace_key_by_mapping(
            dict_obj, mapping)

        self.assertEqual(len(new_keys), len(dict_obj.keys()))
        self.assertEqual(sorted(new_keys), sorted(dict_obj.keys()))

    def test_replace_keys_reverse_order(self):
        dict_obj = {
            "project_id": "demo",
            "ram": "16G"
        }
        new_keys = ["tenantId", "memory"]
        mapping = [(n, o) for o, n in zip(dict_obj.keys(), new_keys)]
        util.VimDriverUtils.replace_key_by_mapping(
            dict_obj, mapping, reverse=True)

        self.assertEqual(len(new_keys), len(dict_obj.keys()))
        self.assertEqual(sorted(new_keys), sorted(dict_obj.keys()))
