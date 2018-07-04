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

from __future__ import absolute_import, unicode_literals

import time
import logging
import json
import urllib2

logger = logging.getLogger(__name__)

def publishAnyEventToVES(ves_subscription, event):
    logger.info("Start to send single event to VES collector.")
    endpoint = ves_subscription.get("endpoint", None)
    username = ves_subscription.get("username", None)
    password = ves_subscription.get("password", None)

    if endpoint:
        try:
            logger.info("publish event to VES: %s", )
            headers = {'Content-Type': 'application/json'}
            request = urllib2.Request(url=endpoint, headers=headers, data=json.dumps(event))
            time.sleep(1)
            response = urllib2.urlopen(request)
            logger.info("VES response is: %s", response.read())
        except urllib2.URLError, e:
            logger.critical("Failed to publish to %s: %s", endpoint, e.reason)
        except Exception as e:
            logger.error("exception:%s" % str(e))
    else:
        logger.info("Missing VES info.")