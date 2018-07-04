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


logger = logging.getLogger(__name__)

### build backlog with domain:"fault", type:"vm"

def buildBacklog_fault_vm(vimid, backlog_input):

    logger.info("vimid: %s" % vimid)
    logger.debug("with input: %s" % backlog_input)

    try:

        #must resolve the tenant id and server id while building the backlog
        tenant_id = backlog_input.get("tenantid", None)
        server_id = backlog_input.get("sourceid", None)

        # should resolve the name to id later
        if tenant_id is None:
            tenant_name = backlog_input["tenant"]
            server_name = backlog_input["source"]

            if tenant_name is None or server_name is None:
                logger.warn("tenant and source should be provided as backlog config")
                return None

            # get token
            #TBD resolve tenant_name to tenant_id

            if server_id is None:
                #TBD resolve server_name to server_id
                pass

        #m.c. proxied OpenStack API
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

