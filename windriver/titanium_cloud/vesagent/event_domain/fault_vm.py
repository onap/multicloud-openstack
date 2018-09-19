#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import json
import uuid
import time

from django.conf import settings
from titanium_cloud.vesagent.vespublish import publishAnyEventToVES
from common.utils import restcall

import datetime
import time
def get_epoch_now_usecond():
    '''
    get epoch timestamp of this moment in usecond
    :return:
    '''
    now_time = datetime.datetime.now()
    epoch_time_sec = time.mktime(now_time.timetuple())
    return int(epoch_time_sec * 1e6 + now_time.microsecond)

logger = logging.getLogger(__name__)

### build backlog with domain:"fault", type:"vm"

def buildBacklog_fault_vm(vimid, backlog_input):

    logger.info("vimid: %s" % vimid)
    logger.debug("with input: %s" % backlog_input)

    try:

        #must resolve the tenant id and server id while building the backlog
        tenant_id = backlog_input.get("tenantid", None)
        server_id = backlog_input.get("sourceid", None)
        server_name = backlog_input.get("source", None)

        # should resolve the name to id later
        if tenant_id is None:
            tenant_name = backlog_input["tenant"]

            # get token
            # resolve tenant_name to tenant_id
            auth_api_url_format = "/{f_vim_id}/identity/v2.0/tokens"
            auth_api_url = auth_api_url_format.format(f_vim_id=vimid)
            auth_api_data = { "auth":{"tenantName": tenant_name} }
            base_url = settings.MULTICLOUD_PREFIX
            extra_headers = ''
            ret = restcall._call_req(base_url, "", "", 0, auth_api_url, "POST", extra_headers, json.dumps(auth_api_data))
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

        #m.c. proxied OpenStack API
        if server_id is None and server_name is None:
            # monitor all VMs of the specified VIMs since no server_id can be resolved
            api_url_fmt = "/{f_vim_id}/compute/v2.1/{f_tenant_id}/servers/detail"
            api_url = api_url_fmt.format(
                f_vim_id=vimid, f_tenant_id=tenant_id)
        else:
            api_url_fmt = "/{f_vim_id}/compute/v2.1/{f_tenant_id}/servers/{f_server_id}"
            api_url = api_url_fmt.format(
                            f_vim_id=vimid, f_tenant_id=tenant_id, f_server_id=server_id)

        backlog = {
            "backlog_uuid":str(uuid.uuid3(uuid.NAMESPACE_URL,
                                          str("%s-%s-%s"%(vimid, tenant_id,server_id)))),
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


### process backlog with domain:"fault", type:"vm"



def processBacklog_fault_vm(vesAgentConfig, vesAgentState, oneBacklog):
    logger.debug("vesAgentConfig:%s, vesAgentState:%s, oneBacklog: %s"
                 % (vesAgentConfig, vesAgentState, oneBacklog))

    try:
        vimid = vesAgentConfig["vimid"]
        tenant_name = oneBacklog["tenant"]

        # get token
        auth_api_url_format = "/{f_vim_id}/identity/v2.0/tokens"
        auth_api_url = auth_api_url_format.format(f_vim_id=vimid)
        auth_api_data = { "auth":{"tenantName": tenant_name} }
        base_url = settings.MULTICLOUD_PREFIX
        extra_headers = ''
        logger.debug("authenticate with url:%s" % auth_api_url)
        ret = restcall._call_req(base_url, "", "", 0, auth_api_url, "POST", extra_headers, json.dumps(auth_api_data))
        if ret[0] > 0 or ret[1] is None:
            logger.critical("call url %s failed with status %s" % (auth_api_url, ret[0]))

        token_resp = json.JSONDecoder().decode(ret[1])
        logger.debug("authenticate resp: %s" % token_resp)
        token = token_resp["access"]["token"]["id"]

        # collect data by issue API
        api_link = oneBacklog["api_link"]
        method = oneBacklog["api_method"]
        base_url = settings.MULTICLOUD_PREFIX
        data = ''
        extra_headers = {'X-Auth-Token': token}
        #which one is correct? extra_headers = {'HTTP_X_AUTH_TOKEN': token}
        logger.debug("authenticate with url:%s, header:%s" % (auth_api_url,extra_headers))
        ret = restcall._call_req(base_url, "", "", 0, api_link, method, extra_headers, data)
        if ret[0] > 0 or ret[1] is None:
            logger.critical("call url %s failed with status %s" % (api_link, ret[0]))

        server_resp = json.JSONDecoder().decode(ret[1])
        logger.debug("collected data: %s" % server_resp)

        # encode data
        backlog_uuid = oneBacklog.get("backlog_uuid", None)
        backlogState = vesAgentState.get("%s" % (backlog_uuid), None)

        #iterate all VMs
        all_events = []
        server_1 = server_resp.get("server",None) # in case querying single server
        for s in server_resp.get("servers",[server_1] if server_1 else []):
            server_id = s.get("id", None)
            server_name = s.get("name", None)
            if not server_id:
                continue

            last_event = backlogState.get("last_event_%s" % (server_id), None)
            logger.debug("last event for server name %s: %s" % (server_name, last_event))

            this_event = data2event_fault_vm(vimid, oneBacklog, last_event, s)
            if this_event is not None:
                logger.debug("this event: %s" % this_event)
                all_events.append(this_event.get("event", None))
                backlogState["last_event_%s" % (server_id)] = this_event

        # report data to VES
        if len(all_events) > 0:
            ves_subscription = vesAgentConfig.get("subscription", None)
            publishAnyEventToVES(ves_subscription, all_events)
            # store the latest data into cache, never expire

    except  Exception as e:
        logger.error("exception:%s" % str(e))
        return

    logger.info("return")
    return


def data2event_fault_vm(vimid, oneBacklog, last_event, vm_data):

    VES_EVENT_VERSION = 3.0
    VES_EVENT_FAULT_VERSION = 2.0
    VES_EVENT_FAULT_DOMAIN = "fault"

    try:

        if vm_status_is_fault(vm_data["status"]):
            if last_event is not None \
                    and last_event['event']['commonEventHeader']['eventName'] == 'Fault_MultiCloud_VMFailure':
                # asserted alarm already, so no need to assert it again
                return None

            eventName = "Fault_MultiCloud_VMFailure"
            priority = "High"
            eventSeverity = "CRITICAL"
            alarmCondition = "Guest_Os_Failure"
            vfStatus = "Active"
            specificProblem = "Fault_MultiCloud_VMFailure"
            eventType = ''
            reportingEntityId = vimid
            reportingEntityName = vimid
            sequence = 0

            startEpochMicrosec = get_epoch_now_usecond()
            lastEpochMicrosec = startEpochMicrosec

            eventId = str(uuid.uuid4())
            pass
        else:
            if last_event is None \
                    or last_event['event']['commonEventHeader']['eventName'] != 'Fault_MultiCloud_VMFailure':
                # not assert alarm yet, so no need to clear it
                return None


            eventName = "Fault_MultiCloud_VMFailureCleared"
            priority = "Normal"
            eventSeverity = "NORMAL"
            alarmCondition = "Vm_Restart"
            vfStatus = "Active"
            specificProblem = "Fault_MultiCloud_VMFailure"
            eventType = ''
            reportingEntityId = vimid
            reportingEntityName = vimid
            sequence = 1 #last_event['event']['commonEventHeader']['sequence'] + 1

            startEpochMicrosec = last_event['event']['commonEventHeader']['startEpochMicrosec']
            lastEpochMicrosec = get_epoch_now_usecond()
            # holmes requires that eventId must be unique for each event!
            eventId = str(uuid.uuid4())

            pass

        # now populate the event structure
        this_event = {
            'event': {
                'commonEventHeader': {
                    'version': VES_EVENT_VERSION,
                    'eventName': eventName,
                    'domain': VES_EVENT_FAULT_DOMAIN,
                    'eventId': eventId,
                    'eventType': eventType,
                    'sourceId': vm_data['id'],
                    'sourceName': vm_data['name'],
                    'reportingEntityId': reportingEntityId,
                    'reportingEntityName': reportingEntityName,
                    'priority': priority,
                    'startEpochMicrosec': startEpochMicrosec,
                    'lastEpochMicrosec': lastEpochMicrosec,
                    'sequence': sequence
                },
                'faultFields': {
                    'faultFieldsVersion': VES_EVENT_FAULT_VERSION,
                    'eventSeverity': eventSeverity,
                    'eventSourceType': 'virtualMachine',
                    'alarmCondition': alarmCondition,
                    'specificProblem': specificProblem,
                    'vfStatus': 'Active',
                    "alarmInterfaceA": "aaaa",
                    "alarmAdditionalInformation": [
                        {
                            "name": "objectType",
                            "value": "VIM"
                        },
                        {
                            "name": "eventTime",
                            "value": str(datetime.datetime.now())
                        }
                    ],
                }

            }

        }

        return this_event

    except Exception as e:
        logger.error("exception:%s" % str(e))
        return None


def vm_status_is_fault(status):
    '''
    report VM fault when status falls into one of following state
        ['ERROR', 'DELETED', 'PAUSED', 'REBUILD', 'RESCUE',
                  'RESIZE','REVERT_RESIZE', 'SHELVED', 'SHELVED_OFFLOADED',
                  'SHUTOFF', 'SOFT_DELETED','SUSPENDED', 'UNKNOWN', 'VERIFY_RESIZE']
    :param status:
    :return:
    '''
    if status in ['BUILD', 'ACTIVE', 'HARD_REBOOT', 'REBOOT', 'MIGRATING', 'PASSWORD']:
        return False
    else:
        return True
