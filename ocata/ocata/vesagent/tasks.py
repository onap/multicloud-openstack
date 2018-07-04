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

### VES agent workers
from __future__ import absolute_import, unicode_literals
from ocata.celery import app
import os
import logging
import json
import time

from django.core.cache import cache

from ocata.vesagent.event_domain.fault_vm import processBacklog_fault_vm

logger = logging.getLogger(__name__)


@app.task(bind=True)
def scheduleBacklogs(self, vimid):
    # make sure only one task runs here
    # cannot get vimid ? logger.info("schedule with vimid:%" % (vimid))

    logger.debug("scheduleBacklogs starts")
    backlog_count, next_time_slot = processBacklogs()
    logger.debug("processBacklogs return with %s, %s" % (backlog_count, next_time_slot))

    # sleep for next_time_slot
    while backlog_count > 0:
        time.sleep(next_time_slot)
        backlog_count, next_time_slot = processBacklogs()

    logger.debug("scheduleBacklogs stops")


def processBacklogs():
    # find out count of valid backlog and the next time slot
    backlog_count = 0
    next_time_slot = 10
    try:
        #get the whole list of backlog
        VesAgentBacklogsVimListStr = cache.get("VesAgentBacklogs.vimlist")
        if VesAgentBacklogsVimListStr is None:
            logger.warn("VesAgentBacklogs.vimlist cannot be found in cache")
            return 0,next_time_slot

        logger.debug("VesAgentBacklogs.vimlist: %s" % (VesAgentBacklogsVimListStr))

        backlogsAllVims = json.loads(VesAgentBacklogsVimListStr)
        if backlogsAllVims is None:
            logger.warn("VesAgentBacklogs.vimlist is empty")
            return 0,next_time_slot

        for vimid in backlogsAllVims:
            #iterate each backlogs
            backlog_count_tmp,next_time_slot_tmp = processBacklogsOfOneVIM(vimid)
            logger.debug("vimid:%s, backlog_count,next_time_slot:%s,%s"
                         %( vimid,backlog_count_tmp,next_time_slot_tmp ))
            backlog_count += backlog_count_tmp
            next_time_slot = next_time_slot_tmp if next_time_slot > next_time_slot_tmp else next_time_slot
            pass

    except Exception as e:
        logger.error("exception:%s" % str(e))

    return backlog_count, next_time_slot

    pass


def processBacklogsOfOneVIM(vimid):
    '''
    process all backlogs for a VIM, return count of valid backlogs
    :param vimid:
    :return:
    '''
    backlog_count = 0
    next_time_slot = 10

    try:
        vesAgentConfigStr = cache.get("VesAgentBacklogs.config.%s" % (vimid))
        if vesAgentConfigStr is None:
            logger.warn("VesAgentBacklogs.config.%s cannot be found in cache" % (vimid))
            return 0,next_time_slot

        logger.debug("VesAgentBacklogs.config.%s: %s" % (vimid, vesAgentConfigStr))

        vesAgentConfig = json.loads(vesAgentConfigStr)
        if vesAgentConfig is None:
            logger.warn("VesAgentBacklogs.config.%s corrupts" % (vimid))
            return 0,next_time_slot


        vesAgentStateStr = cache.get("VesAgentBacklogs.state.%s" % (vimid))
        vesAgentState = json.loads(vesAgentStateStr) if vesAgentStateStr is not None else {}

        ves_info = vesAgentConfig.get("subscription", None)
        if ves_info is None:
            logger.warn("VesAgentBacklogs.config.%s: ves subscription corrupts:%s" % (vimid, vesAgentConfigStr))
            return 0,next_time_slot

        poll_interval_default = vesAgentConfig.get("poll_interval_default", None)
        if poll_interval_default is None:
            logger.warn("VesAgentBacklogs.config.%s: poll_interval_default corrupts:%s" % (vimid, vesAgentConfigStr))
            return 0,next_time_slot

        if poll_interval_default == 0:
            # invalid interval value
            logger.warn("VesAgentBacklogs.config.%s: poll_interval_default invalid:%s" % (vimid, vesAgentConfigStr))
            return 0,next_time_slot

        backlogs_list = vesAgentConfig.get("backlogs", None)
        if backlogs_list is None:
            logger.warn("VesAgentBacklogs.config.%s: backlogs corrupts:%s" % (vimid, vesAgentConfigStr))
            return 0,next_time_slot

        for backlog in backlogs_list:
            backlog_count_tmp, next_time_slot_tmp = processOneBacklog(
                               vesAgentConfig, vesAgentState, poll_interval_default, backlog)
            logger.debug("processOneBacklog return with %s,%s" % (backlog_count_tmp, next_time_slot_tmp))
            backlog_count += backlog_count_tmp
            next_time_slot = next_time_slot_tmp if next_time_slot > next_time_slot_tmp else next_time_slot

            pass

        # save back the updated backlogs state
        vesAgentStateStr = json.dumps(vesAgentState)
        cache.set("VesAgentBacklogs.state.%s" % vimid, vesAgentStateStr, None)

    except Exception as e:
        logger.error("exception:%s" % str(e))

    return backlog_count, next_time_slot


def processOneBacklog(vesAgentConfig, vesAgentState, poll_interval_default, oneBacklog):
    logger.info("Process one backlog")
    #logger.debug("vesAgentConfig:%s, vesAgentState:%s, poll_interval_default:%s, oneBacklog: %s"
    #             % (vesAgentConfig, vesAgentState, poll_interval_default, oneBacklog))

    backlog_count = 1
    next_time_slot = 10
    try:
        timestamp_now = int(time.time())
        backlog_uuid = oneBacklog.get("backlog_uuid", None)
        if backlog_uuid is None:
            # warning: uuid is None, omit this backlog
            logger.warn("backlog without uuid: %s" % oneBacklog)
            return 0, next_time_slot

        backlogState = vesAgentState.get("%s" % (backlog_uuid), None)
        if backlogState is None:
            initialBacklogState = {
                "timestamp": timestamp_now
            }
            vesAgentState["%s" % (backlog_uuid)] = initialBacklogState
            backlogState = initialBacklogState

        time_expiration = backlogState["timestamp"] \
                          + oneBacklog.get("poll_interval", poll_interval_default)
        # check if poll interval expires
        if timestamp_now < time_expiration:
            # not expired yet
            logger.info("return without dispatching, not expired yet")
            return backlog_count, next_time_slot

        logger.info("Dispatching backlog")

        # collect data in case of expiration
        if oneBacklog["domain"] == "fault" and oneBacklog["type"] == "vm":
            processBacklog_fault_vm(vesAgentConfig, vesAgentState, oneBacklog)
        else:
            logger.warn("Dispatching backlog fails due to unsupported backlog domain %s,type:%s"
                        % (oneBacklog["domain"], oneBacklog["type"]))
            backlog_count = 0
            pass

        # update timestamp and internal state
        backlogState["timestamp"] = timestamp_now
    except Exception as e:
        logger.error("exception:%s" % str(e))

    logger.info("return")
    return backlog_count, next_time_slot

