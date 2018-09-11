# Copyright (c) Intel Corporation, Inc.
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

import mock

import unittest
import json

from ocata.vesagent.vespublish import publishAnyEventToVES
from common.utils.restcall import _call_req
from ocata.vesagent.event_domain import fault_vm



class FaultVMTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_epoch_now_usecond(self):
        epoch = fault_vm.get_epoch_now_usecond()
        self.assertGreater(epoch, 1)
        pass
