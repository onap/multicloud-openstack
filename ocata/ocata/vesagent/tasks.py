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

logger = logging.getLogger(__name__)


@app.task(bind=True)
def scheduleBacklogs(self, vimid):
    # make sure only one task runs here
    logger.info("schedule with vimid:%" % (vimid))

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
    backlog_count = 3
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



    except Exception as e:
        logger.error("exception:%s" % str(e))

    return backlog_count, next_time_slot

