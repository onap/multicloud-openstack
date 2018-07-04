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
    backlog_count = 2 #debug the timer sleep
    next_time_slot = 10

    logger.debug("process backlogs starts")

    #TBD

    logger.debug("return with %s" %(backlog_count, next_time_slot))
    return backlog_count, next_time_slot

