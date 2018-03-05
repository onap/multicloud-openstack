# Copyright 2017-2018 Wind River Systems, Inc.
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
from newton_base.extensions import extensions as newton_extensions

logger = logging.getLogger(__name__)

DEBUG=True

class Extensions(newton_extensions.Extensions):

    def __init__(self):
        self._logger = logger
        self.proxy_prefix = settings.MULTICLOUD_PREFIX

