# Copyright (c) 2017-2019 Wind River Systems, Inc.
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

from django.conf.urls import include, url
from fcaps.vesagent import vesagent_ctrl

urlpatterns = [
    url(r'^', include('fcaps.samples.urls')),

    url(r'^api/multicloud-fcaps/v0/(?P<vimid>[0-9a-zA-Z_-]+)/vesagent/?$',
        vesagent_ctrl.VesAgentCtrl.as_view()),

    url(r'^api/multicloud-fcaps/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/vesagent/?$',
        vesagent_ctrl.APIv1VesAgentCtrl.as_view()),

]
