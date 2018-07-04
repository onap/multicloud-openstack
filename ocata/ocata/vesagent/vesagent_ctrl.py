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

import logging
import traceback
import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings
from common.msapi import extsys


logger = logging.getLogger(__name__)

class VesAgentCtrl(APIView):
    '''
    control plane of VesAgent
    Design tips:
    1, vesagent are multiple processing workers
    2, the runtime logic is simple: a vesagent worker polls the data source (vm/hypervisor/host/vim/etc.)
    and then feeds the encoded data to VES.
    3, the vesagent workers can be distributed to different clouds while latency/throughput is concerned,
    this distributed deployment usually comes along with the distributed VES deployment.
    So it is very likely that the collected data from different VIM/Cloud instance will be fed into
    different VES endpoint, however, assuming that there will be at most one VES endpoint serving
    any single VIM/Cloud instance.
    4, According to VES specs, the collected data can be cataloged by domain:
        domain : fault, heartbeat, measurementsForVfScaling, other, stateChange, syslog, thresholdCrossingAlert
        As far as VIM/Cloud concerned, fault, heartbeat, measurementsForVfScaling, TCAalert are relevant.
    5, the source of the collected data can be cataloged by eventSourceType:
        eventSourceType: VNF/VNFC/VM
        As far as VIM/Cloud concerned, only VM is relevant. This eventSourceType should be extended to cover
        the data source of hypervisor, VIM, Host,Controller, PIM, etc.

    6, the source of collected data should be specified explicitly,so is the domain of the collected data.
        To specify the source: eventSourceType, uuid or name of the source
        To specify the domain: domain
        the specifications above will be provisioned as a vesagent backlog entry to a VIM/Cloud instance
        to tell a vesagent worker that :
        with regarding to that VIM/Cloud instance, what kind of data to be collected from which source .

    7,the VES endpoint will be also specified for a VIM/Cloud instance, so that all collected data
    will be fed into this VES endpoint

    8, the vesagent backlog are stored into the respective cloud_region's property "cloud-extra-info",
     which implies that those specifications can be CRUD either by ESR portal or the RestAPIs in this view, e.g.
        "cloud-extra-info": {
            ...,
            "vesagent_config":
            {
                "ves_subscription":{
                    "endpoint":"http://{VES IP}:{VES port}/{URI}",
                    "username":"{VES username}",
                    "password":"{VES password}",
                },
                "poll_interval_default" : "{default interval for polling}",
                "backlogs":[
                    {
                        "domain":"fault"
                        "type":"vm",
                        "tenant":"{tenant name1}",
                        "source":"{VM name1}",
                        "poll_interval" : "{optional, interval for polling}",
                    },
                    {
                        "domain":"fault"
                        "type":"vm",
                        "tenant":"{tenant name2}",
                        "source":"{VM name2}",
                        "poll_interval" : "{optional, interval for polling}",
                    }
                ]
            }
        }

        Idea: API dispatching to distributed M.C. service can be determined by Complex Object in AAI:
            cloud-region has been assoicated to a Complex Object
            M.C. plugin service instance should refer to the same Complex Object (by physical_locaton_id ?)
            So the M.C. broker/API distributor/other approach will correlate the cloud-region with
            corresponding M.C. plugin service instance.


    Backlog built in cache:

        maintain backlog in cache and VES agent workers
        cache objects:
            "VesAgentBacklogs.vimlist": [ list of vimid] ### will not expire forever
            "VesAgentBacklogs.state.{vimdid}":
            ### will expire eventually to eliminate the garbage, expiration duration: 1hour?
            {
                "{backlog_uuid}": {
                    "timestamp": "{timestamp for last time of data collecting}",
                    "api_data": [list of data to populate the format string of the API link]
                    "last_event": {object, event reported to ves last time}"
                }
            }
            "VesAgentBacklogs.config.{vimdid}": ### will not expire forever
            {
                "vimid": "{vim id}",
                "subscription": {
                    "endpoint": "{ves endpoint, e.g. http://ves_ip:ves_port/eventListener/v5}",
                    "username": "{username}",
                    "password": "{password}"
                }
                "poll_interval_default" : "{default interval for polling}",
                "backlogs":[
                    {
                        "backlog_uuid": "{uuid to identify the backlog}"
                        "domain":"fault"
                        "type":"vm",
                        "tenant":"{tenant name1}",
                        "source":"{VM name1}",
                        "poll_interval" : "{optional, interval in second for polling}",
                        "api_method": "{GET/POST/PUT/etc.}",
                        "api_link":"{API link to collect data, could be format string}",
                        "tenant_id": tenant_id,
                        "server_id": server_id,
                    },
                    {
                        "domain":"fault"
                        "type":"vm",
                        "tenant":"{tenant name2}",
                        "source":"{VM name2}",
                        "poll_interval" : "{optional, interval in second for polling}",
                        "api_method": "{GET/POST/PUT/etc.}",
                        "api_link":"{API link to collect data, could be format string}",
                        "tenant_id": tenant_id,
                        "server_id": server_id,
                    }
                ]
            }
    '''

    def __init__(self):
        self._logger = logger
        self.proxy_prefix = settings.MULTICLOUD_PREFIX


    def get(self, request, vimid=""):
        '''
        get blob of vesagent-config
        :param request:
        :param vimid:
        :return:
        '''
        self._logger.info("vimid: %s" % vimid)
        self._logger.debug("with META: %s" % request.META)

        pass


    def post(self, request, vimid=""):
        '''
        update the blob of vesagent-config, rebuild the backlog for the vesagent workers,
        and start the vesagent workers if not started yet
        Implication: the request to this API endpoint will build the backlog locally, hence only local VES agent workers
        will process these backlogs, which conforms to distributed deployment of M.C. services which includes VES agents
        :param request:{"vesagent_config":
                         {"ves_subscription":
                           {"endpoint":"http://127.0.0.1:9005/sample",
                            "username":"user","password":"password"},
                            "poll_interval_default":10,
                            "backlogs":
                            [
                            {"domain":"fault","type":"vm","tenant":"VIM","source":"onap-aaf"}
                            ]
                           }
                         }
        :param vimid:
        :return:
        '''
        self._logger.info("vimid: %s" % vimid)
        self._logger.debug("with META: %s, with data: %s" % (request.META, request.data))

        pass

    def delete(self, request, vimid=""):
        '''
        delete the blob of vesagent-config, remove it from backlog and stop the vesagent worker if no backlog
        :param request:
        :param vimid:
        :return:
        '''
        self._logger.info("vimid: %s" % vimid)
        self._logger.debug("with META: %s" % request.META)

        return Response(status=status.HTTP_200_OK)

