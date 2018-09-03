# Copyright (c) 2017-2018 Wind River Systems, Inc.
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

from titanium_cloud.registration.views import registration
from newton_base.openoapi import tenants
from titanium_cloud.resource.views import capacity
from titanium_cloud.vesagent import vesagent_ctrl
from titanium_cloud.resource.views import infra_workload

urlpatterns = [
    url(r'^', include('titanium_cloud.swagger.urls')),
    url(r'^', include('titanium_cloud.samples.urls')),

    # API v0, depreciated due to MULTICLOUD-335
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/registry/?$',
        registration.APIv0Registry.as_view()),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/?$',
        registration.APIv0Registry.as_view()),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/exten',
        include('titanium_cloud.extensions.urls')),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/',
             include('titanium_cloud.proxy.urls')),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/tenants/?$',
             tenants.Tenants.as_view()),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/'
        '(?P<tenantid>[0-9a-zA-Z_-]{20,})/', include('titanium_cloud.requests.urls')),
    # CapacityCheck
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/capacity_check/?$',
        capacity.CapacityCheck.as_view()),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/vesagent/?$',
        vesagent_ctrl.VesAgentCtrl.as_view()),

    # API v1, depreciated due to MULTICLOUD-335
    url(r'^api/multicloud-titanium_cloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/registry/?$',
        registration.APIv1Registry.as_view()),
    url(r'^api/multicloud-titanium_cloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/?$',
        registration.APIv1Registry.as_view()),
    url(r'^api/multicloud-titanium_cloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/exten',
        include('titanium_cloud.extensions.urlsV1')),
    url(r'^api/multicloud-titanium_cloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/',
        include('titanium_cloud.proxy.urlsV1')),
    url(r'^api/multicloud-titanium_cloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/tenants/?$',
        tenants.APIv1Tenants.as_view()),
    url(r'^api/multicloud-titanium_cloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/'
        '(?P<tenantid>[0-9a-zA-Z_-]{20,})/', include('titanium_cloud.requests.urlsV1')),
    # CapacityCheck
    url(r'^api/multicloud-titanium_cloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/capacity_check/?$',
        capacity.APIv1CapacityCheck.as_view()),
    url(r'^api/multicloud-titanium_cloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/vesagent/?$',
        vesagent_ctrl.APIv1VesAgentCtrl.as_view()),
    url(r'^api/multicloud-titanium_cloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/infra_workload/?$',
        infra_workload.APIv1InfraWorkload.as_view()),

    # API v0, new namespace due to MULTICLOUD-335
    url(r'^api/multicloud-titaniumcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/registry/?$',
        registration.APIv0Registry.as_view()),
    url(r'^api/multicloud-titaniumcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/?$',
        registration.APIv0Registry.as_view()),
    url(r'^api/multicloud-titaniumcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/exten',
        include('titanium_cloud.extensions.urls')),
    url(r'^api/multicloud-titaniumcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/',
             include('titanium_cloud.proxy.urls')),
    url(r'^api/multicloud-titaniumcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/tenants/?$',
             tenants.Tenants.as_view()),
    url(r'^api/multicloud-titaniumcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/'
        '(?P<tenantid>[0-9a-zA-Z_-]{20,})/', include('titanium_cloud.requests.urls')),
    # CapacityCheck
    url(r'^api/multicloud-titaniumcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/capacity_check/?$',
        capacity.CapacityCheck.as_view()),
    url(r'^api/multicloud-titaniumcloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/vesagent/?$',
        vesagent_ctrl.VesAgentCtrl.as_view()),

    # API v1, new namespace due to MULTICLOUD-335
    url(r'^api/multicloud-titaniumcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/registry/?$',
        registration.APIv1Registry.as_view()),
    url(r'^api/multicloud-titaniumcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/?$',
        registration.APIv1Registry.as_view()),
    url(r'^api/multicloud-titaniumcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/exten',
        include('titanium_cloud.extensions.urlsV1')),
    url(r'^api/multicloud-titaniumcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/',
        include('titanium_cloud.proxy.urlsV1')),
    url(r'^api/multicloud-titaniumcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/tenants/?$',
        tenants.APIv1Tenants.as_view()),
    url(r'^api/multicloud-titaniumcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/'
        '(?P<tenantid>[0-9a-zA-Z_-]{20,})/', include('titanium_cloud.requests.urlsV1')),
    # CapacityCheck
    url(r'^api/multicloud-titaniumcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/capacity_check/?$',
        capacity.APIv1CapacityCheck.as_view()),
    url(r'^api/multicloud-titaniumcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/vesagent/?$',
        vesagent_ctrl.APIv1VesAgentCtrl.as_view()),
    url(r'^api/multicloud-titaniumcloud/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/infra_workload/?$',
        infra_workload.APIv1InfraWorkload.as_view()),
]
