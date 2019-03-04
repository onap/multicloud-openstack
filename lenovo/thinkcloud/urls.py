# Copyright (c) 2017-2018 Lenovo Systems, Inc.
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

from thinkcloud.registration.views import registration
from newton_base.openoapi import tenants
from thinkcloud.resource.views import capacity
from thinkcloud.resource.views import events
from thinkcloud.vesagent import vesagent_ctrl
from thinkcloud.resource.views import infra_workload

urlpatterns = [
    url(r'^', include('thinkcloud.swagger.urls')),
    url(r'^', include('thinkcloud.samples.urls')),
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/registry$',
        registration.Registry.as_view()),
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)$',
        registration.Registry.as_view()),
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/exten',
        include('thinkcloud.extensions.urls')),
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/infra_workload/?$',
        infra_workload.InfraWorkload.as_view()),
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/infra_workload/(?P<requri>[0-9a-zA-Z_-]*)/?$',
        infra_workload.InfraWorkload.as_view()),
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/',
        include('thinkcloud.proxy.urls')),
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/tenants$',
        tenants.Tenants.as_view()),
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/'
        '(?P<tenantid>[0-9a-zA-Z_-]{20,})/', include('thinkcloud.requests.urls')),
    # CapacityCheck
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/capacity_check/?$',
        capacity.CapacityCheck.as_view()),
    # events
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/events_check/?$',
        events.EventsCheck.as_view()),
    url(r'^api/multicloud-thinkcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/vesagent/?$',
        vesagent_ctrl.VesAgentCtrl.as_view()),

    # API upgrading
    url(r'^api/multicloud-thinkcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/registry$',
        registration.RegistryV1.as_view()),
    url(r'^api/multicloud-thinkcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)$',
        registration.RegistryV1.as_view()),
    url(r'^api/multicloud-thinkcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/exten',
        include('thinkcloud.extensions.urlsV1')),
    url(r'^api/multicloud-thinkcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/tenants/?$',
        tenants.APIv1Tenants.as_view()),
    url(r'^api/multicloud-thinkcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/'
        '(?P<tenantid>[0-9a-zA-Z_-]{20,})/', include('thinkcloud.requests.urlsV1')),
    url(r'^api/multicloud-thinkcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/capacity_check/?$',
        capacity.APIv1CapacityCheck.as_view()),
    url(r'^api/multicloud-thinkcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/vesagent/?$',
        vesagent_ctrl.APIv1VesAgentCtrl.as_view()),
    url(r'^api/multicloud-thinkcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/infra_workload/?$',
        infra_workload.APIv1InfraWorkload.as_view()),
    url(r'^api/multicloud-thinkcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/infra_workload/(?P<requri>[0-9a-zA-Z_-]*)/?$',
        infra_workload.APIv1InfraWorkload.as_view()),
    url(r'^api/multicloud-thinkcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/',
        include('thinkcloud.proxy.urlsV1')),
]
