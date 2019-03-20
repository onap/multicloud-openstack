#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2019, CMCC Technologies Co., Ltd.

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
import json
import uuid

from django.conf import settings
from fcaps.vesagent.vespublish import publishAnyEventToVES
from common.utils import restcall
from common.msapi.helper import Helper as helper


import datetime
import time

logger = logging.getLogger(__name__)


def get_epoch_now_usecond():
    '''
    get epoch timestamp of this moment in usecond
    :return:
    '''
    now_time = datetime.datetime.now()
    epoch_time_sec = time.mktime(now_time.timetuple())
    return int(epoch_time_sec * 1e6 + now_time.microsecond)


def buildBacklog_pm_vm(vimid, backlog_input):
    # build backlog with domain:"fault", type:"vm"

    logger.info("vimid: %s" % vimid)
    logger.debug("with input: %s" % backlog_input)

    try:

        # must resolve the tenant id and server id while building the backlog
        tenant_id = backlog_input.get("tenantid", None)
        server_id = backlog_input.get("sourceid", None)
        server_name = backlog_input.get("source", None)

        # should resolve the name to id later
        if tenant_id is None:
            tenant_name = backlog_input["tenant"]

            # resolve tenant_name to tenant_id
            auth_api_url_format = "/{f_vim_id}/identity/v2.0/tokens"
            auth_api_url = auth_api_url_format.format(f_vim_id=vimid)
            auth_api_data = {"auth": {"tenantName": tenant_name}}
            base_url = settings.MULTICLOUD_PREFIX
            extra_headers = ''
            ret = restcall._call_req(base_url, "", "", 0, auth_api_url,
                                     "POST", extra_headers, json.dumps(auth_api_data))
            if ret[0] > 0 or ret[1] is None:
                logger.critical("call url %s failed with status %s" % (auth_api_url, ret[0]))
                return None

            token_resp = json.JSONDecoder().decode(ret[1])
            token = token_resp["access"]["token"]["id"]
            tenant_id = token_resp["access"]["token"]["tenant"]["id"]

            if server_id is None and server_name:
                # resolve server_name to server_id in case no wildcast in server_name
                vserver_api_url_format \
                    = "/{f_vim_id}/compute/v2.1/{f_tenant_id}/servers?name={f_server_name}"
                vserver_api_url = vserver_api_url_format.format(f_vim_id=vimid,
                                                                f_tenant_id=tenant_id,
                                                                f_server_name=server_name)
                base_url = settings.MULTICLOUD_PREFIX
                extra_headers = {'X-Auth-Token': token}
                ret = restcall._call_req(base_url, "", "", 0, vserver_api_url, "GET", extra_headers, "")
                if ret[0] > 0 or ret[1] is None:
                    logger.critical("call url %s failed with status %s" % (vserver_api_url, ret[0]))
                    return None

                server_resp = json.JSONDecoder().decode(ret[1])
                # find out the server wanted
                for s in server_resp.get("servers", []):
                    if s["name"] == server_name:
                        server_id = s["id"]
                        break
                if server_id is None:
                    logger.warn("source %s cannot be found under tenant id %s "
                                % (server_name, tenant_id))
                    return None

        # m.c. proxied OpenStack API
        if server_id is None and server_name is None:
            api_url = "/v2/samples"

        else:
            # monitor all VMs of the specified VIMs since no server_id can be resolved
            api_url_fmt = "/v2/samples?q.field=resource_id&q.op=eq&q.value={f_server_id}"
            api_url = api_url_fmt.format(
                f_server_id=server_id)


        backlog = {
            "backlog_uuid":
                str(uuid.uuid3(uuid.NAMESPACE_URL,
                               str("%s-%s-%s" % (vimid, tenant_id, server_id)))),
            "tenant_id": tenant_id,
            "server_id": server_id,
            "api_method": "GET",
            "api_link": api_url,
        }
        backlog.update(backlog_input)
    except Exception as e:
        logger.error("exception:%s" % str(e))
        return None

    logger.info("return")
    logger.debug("with backlog: %s" % backlog)
    return backlog


# process backlog with domain:"pm", type:"vm"


def processBacklog_pm_vm(vesAgentConfig, vesAgentState, oneBacklog):
    logger.debug("vesAgentConfig:%s, vesAgentState:%s, oneBacklog: %s"
                 % (vesAgentConfig, vesAgentState, oneBacklog))

    try:

        # get token
        # resolve tenant_name to tenant_id
        cloud_owner, regionid = extsys.decode_vim_id(vimid)
        # should go via multicloud proxy so that the selflink is updated by multicloud
        retcode, v2_token_resp_json, os_status = helper.MultiCloudIdentityHelper(
            settings.MULTICLOUD_API_V1_PREFIX,
            cloud_owner, regionid, "/v2.0/tokens")
        if retcode > 0 or not v2_token_resp_json:
            logger.error("authenticate fails:%s,%s, %s" %
                         (cloud_owner, regionid, v2_token_resp_json))
            return

        service_type = "metering"
        resource_uri = oneBacklog["api_link"]
        template_data = ''
        self._logger.info("retrieve metering resources, URI:%s" % resource_uri)
        retcode, content, os_status = helper.MultiCloudServiceHelper(cloud_owner,
                                                                     regionid,
                                                                     v2_token_resp_json,
                                                                     service_type,
                                                                     resource_uri,
                                                                     template_data,
                                                                     "GET")
        meters = content if retcode == 0 and content else []

        for meter in meters:
            encodeData = data2event_pm_vm(meter)
            encodeData['event']['commonEventHeader']['eventType'] = 'guestOS'
            encodeData['event']['commonEventHeader']['reportingEntityId'] = vimid
            encodeData['event']['commonEventHeader']['reportingEntityName'] = vimid

            if encodeData is not None:
                logger.debug("this event: %s" % encodeData)
                all_events.append(encodeData.get("event", None))

        # report data to VES
        if len(all_events) > 0:
            ves_subscription = vesAgentConfig.get("subscription", None)
            publishAnyEventToVES(ves_subscription, all_events)
            # store the latest data into cache, never expire

    except Exception as e:
        logger.error("exception:%s" % str(e))
        return

    logger.info("return")
    return


def data2event_pm_vm(vm_data):
    VES_EVENT_VERSION = 3.0
    VES_EVENT_pm_VERSION = 2.0
    VES_EVENT_pm_DOMAIN = "measurementsForVfScaling"
    eventId = str(uuid.uuid1())
    eventName = 'Mfvs_' + vm_data['resource_id']
    eventType = ''
    sourceId = vm_data['resource_id']
    sourceName = vm_data['resource_id']
    reportingEntityId = ''
    reportingEntityName = ''
    priority = 'Normal'
    sequence = 1
    startEpochMicrosec = int(time.mktime(time.strptime(vm_data['recorded_at'], '%Y-%m-%dT%H:%M:%S')))
    lastEpochMicrosec = startEpochMicrosec
        # now populate the event structure
    this_event = {
        'event': {
            'commonEventHeader': {
                'version': VES_EVENT_VERSION,
                'eventName': eventName,
                'domain': VES_EVENT_pm_DOMAIN,
                'eventId': eventId,
                'eventType': eventType,
                'sourceId': sourceId,
                'sourceName': sourceName,
                'reportingEntityId': reportingEntityId,
                'reportingEntityName': reportingEntityName,
                'priority': priority,
                'startEpochMicrosec': startEpochMicrosec,
                'lastEpochMicrosec': lastEpochMicrosec,
                'sequence': sequence
            },
            'measurementsForVfScalingFields': {
                'measurementsForVfScalingVersion': VES_EVENT_pm_VERSION,
                'measurementInterval': 0,
                'additionalMeasurements': vm_data['additionalMeasurements']
            }
        }
    }

    return this_event

def partition_samples(data):
    # check all samples recorded at time
    time_sates = []
    for obj in data:
        time_sates.append(obj['recorded_at'])
    time_sates = list(set(time_sates))
    # match time for each sample
    meter_to_ves = []
    for time_sate in time_sates:
        additionalMeasurements = []
        arrayOfFields = []
        resource_id = ""
        for obj in data:
            if obj['recorded_at'] == time_sate:
                arrayOfFields.append({'name':obj['meter'], 'value':str(obj['volume'])})
                resource_id = obj['resource_id']
        additionalMeasurements.append({'name':resource_id, 'arrayOfFields':arrayOfFields})
        meter_to_ves.append({'resource_id':resource_id, 'recorded_at':time_sate, 'additionalMeasurements':additionalMeasurements})
    return meter_to_ves