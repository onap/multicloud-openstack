# Copyright (c) 2017-2018 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import json
import logging
# import re
import uuid
import threading
import datetime
import time
#import traceback

# from common.exceptions import VimDriverNewtonException
from common.utils import restcall

from rest_framework import status
from django.core.cache import cache

logger = logging.getLogger(__name__)


# Helper of MultiCloud API invocation
class Helper(object):

    @staticmethod
    def MultiCloudIdentityHelper(multicloud_api_prefix, cloud_owner,
                                 cloud_region_id, uri, data={}, header=''):
        auth_api_url_format = "/{f_cloudowner}/{f_cloudregionid}/identity{f_uri}"
        auth_api_url = auth_api_url_format.format(f_cloudowner=cloud_owner,
                                                  f_cloudregionid=cloud_region_id,
                                                  f_uri=uri)
        extra_headers = header
        ret = restcall._call_req(multicloud_api_prefix, "", "", 0, auth_api_url, "POST", extra_headers, json.dumps(data))
        if ret[0] == 0 and ret[1]:
            content = json.JSONDecoder().decode(ret[1])
            ret[1] = content
        return ret

    # The consumer of this api must be attaching to the same management network of multicloud,
    # The constraints comes from the returned catalog endpoint url e.g. "http://10.0.14.1:80/api/multicloud-titaniumcloud/v0/pod25_RegionOne/identity/v3"
    @staticmethod
    def MultiCloudServiceHelper(
            cloud_owner, cloud_region_id, v2_token_resp_json, service_type,
            uri, data=None, method="GET"):
        # get endpoint from token response
        token = v2_token_resp_json["access"]["token"]["id"]
        catalogs = v2_token_resp_json["access"]["serviceCatalog"]
        for catalog in catalogs:
            if catalog['type'] == service_type:
                # now we have endpoint
                endpoint_url = catalog['endpoints'][0]['publicURL']
                extra_headers = {'X-Auth-Token': token}
                ret = restcall._call_req(endpoint_url, "", "", 0, uri, method, extra_headers, json.dumps(data) if data else "")
                if ret[0] == 0 and ret[1]:
                    content = json.JSONDecoder().decode(ret[1])
                    ret[1] = content
                return ret
        return [1, None, status.HTTP_404_NOT_FOUND] # return resource not found in case no type found


# Helper of AAI resource access
class MultiCloudAAIHelper(object):
    '''
    Helper to register infrastructure resource into AAI
    '''

    def __init__(self, multicloud_prefix, aai_base_url):
        # logger.debug("MultiCloudAAIHelper __init__ traceback: %s" % traceback.format_exc())
        self.proxy_prefix = multicloud_prefix
        self.aai_base_url = aai_base_url
        self._logger = logger
        # super(MultiCloudAAIHelper, self).__init__()

    def _get_list_resources(
            self, resource_url, service_type, session, viminfo,
            vimid, content_key):
        service = {
            'service_type': service_type,
            'interface': 'public'
        }

        # identity service should not filtered by region since it is might be first call
        # to figure out available region list
        if service_type != 'identity':
            service['region_name'] = viminfo['openstack_region_id']\
                if viminfo.get('openstack_region_id') else viminfo['cloud_region_id']

        self._logger.debug("making request with URI:%s,%s" % (resource_url, service))
        resp = session.get(resource_url, endpoint_filter=service)
        self._logger.debug("request returns with status %s" % resp.status_code)
        if resp.status_code == status.HTTP_200_OK:
            self._logger.debug("with content:%s" % resp.json())
            content = resp.json()
            return content.get(content_key)
        return  None # failed to discover resources

    def _update_resoure(self, cloud_owner, cloud_region_id,
                        resoure_id, resource_info, resource_type):
        if cloud_owner and cloud_region_id:
            self._logger.debug(
                ("_update_resoure,vimid:%(cloud_owner)s"
                 "_%(cloud_region_id)s req_to_aai: %(resoure_id)s, "
                 "%(resource_type)s, %(resource_info)s")
                % {
                    "cloud_owner": cloud_owner,
                    "cloud_region_id": cloud_region_id,
                    "resoure_id": resoure_id,
                    "resource_type": resource_type,
                    "resource_info": resource_info,
                })

            # get the resource first
            resource_url = ("/cloud-infrastructure/cloud-regions/"
                     "cloud-region/%(cloud_owner)s/%(cloud_region_id)s/"
                     "%(resource_type)ss/%(resource_type)s/%(resoure_id)s"
                     % {
                         "cloud_owner": cloud_owner,
                         "cloud_region_id": cloud_region_id,
                         "resoure_id": resoure_id,
                         "resource_type": resource_type,
                     })

            # get cloud-region
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "GET")

            # add resource-version
            if retcode == 0 and content:
                content = json.JSONDecoder().decode(content)
                #resource_info["resource-version"] = content["resource-version"]
                content.update(resource_info)
                resource_info = content

            #then update the resource
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "PUT", content=resource_info)

            # self._logger.debug(
            #     ("_update_resoure,vimid:%(cloud_owner)s"
            #      "_%(cloud_region_id)s req_to_aai: %(resoure_id)s, "
            #      "return %(retcode)s, %(content)s, %(status_code)s")
            #     % {
            #         "cloud_owner": cloud_owner,
            #         "cloud_region_id": cloud_region_id,
            #         "resoure_id": resoure_id,
            #         "retcode": retcode,
            #         "content": content,
            #         "status_code": status_code,
            #     })
            return retcode, content
        # unknown cloud owner,region_id
        return (
            11,
            "Unknown Cloud Region ID: %s ,%s" %(cloud_owner, cloud_region_id)
        )
    pass


# thread helper
class MultiCloudThreadHelper(object):
    '''
    Helper to manage LCM of an offloading thread
    '''

    @staticmethod
    def get_epoch_now_usecond():
        '''
        get epoch timestamp of this moment in usecond
        :return:
        '''
        now_time = datetime.datetime.now()
        epoch_time_sec = time.mktime(now_time.timetuple())
        return int(epoch_time_sec * 1e6 + now_time.microsecond)

    def __init__(self, name=""):
        # debug: dump the callstack to determine the callstack, hence the lcm
        # logger.debug("MultiCloudThreadHelper __init__: %s" % traceback.format_exc())

        # format of a backlog item:
        # {
        #   "id": unique string to identify this item in backlog,
        #   "worker": pointer to helper method
        #   "payload": opaque object to pass to the worker for processing
        #   "repeat": interval in micro-seconds for repeating this worker, 0 for one time worker
        #   "timestamp": time stamp of last invocation of this worker, 0 for initial state
        #   "status": opaque object to represent the progress of the backlog processing
        # }
        # format of backlog:
        # {"<id value of backlog item>": <backlog item>, ...}
        self.name = name or "default"
        self.backlog = {}
        # expired backlog items
        self.expired_backlog = {}
        self.lock = threading.Lock()
        self.state_ = 0  # 0: stopped, 1: started
        self.cache_prefix = "bi_"+self.name+"_"
        self.cache_expired_prefix = "biex_"+self.name+"_"

        self.thread = MultiCloudThreadHelper.HelperThread(self)
        # self.thread.start()

    def state(self):
        return self.state_

    def start(self):
        self.lock.acquire()
        if 0 == self.state_:
            self.state_ = 1
            # self.thread = MultiCloudThreadHelper.HelperThread(self)
            self.thread.start()
        else:
            pass
        self.lock.release()

    def stop(self):
        self.state_ = 0

    def add(self, backlog_item):
        cache_for_query = None
        if not backlog_item.get("worker", None):
            logger.warn("Fail to add backlog item: %s" % backlog_item)
            return None
        if not backlog_item.get("id", None):
            backlog_item["id"] = str(uuid.uuid1())
        else:
            cache_for_query = {
                "id": backlog_item["id"],
                "status": backlog_item.get("status", None)
            }

        if not backlog_item.get("repeat", None):
            backlog_item["repeat"] = 0
        backlog_item["timestamp"] = 0

        # self.lock.acquire()
        # make sure there is no identical backlog in expired backlog
        if cache_for_query:
            cache.set(self.cache_prefix + backlog_item["id"],
                      json.dumps(cache_for_query), 3600 * 24)

        self.expired_backlog.pop(backlog_item["id"], None)
        self.backlog[backlog_item["id"]] = backlog_item
        # self.lock.release()
        logger.debug("Add backlog item: %s" % backlog_item)
        return len(self.backlog)

    def get(self, backlog_id):
        item = self.backlog.get(backlog_id, None) or self.expired_backlog.get(backlog_id, None)

        # check the cache
        if not item:
            cache_for_query_str = cache.get(self.cache_prefix + backlog_id)
            if cache_for_query_str:
                item = json.loads(cache_for_query_str)
            else:
                cache_for_query_str = cache.get(self.cache_expired_prefix + backlog_id)
                if cache_for_query_str:
                    item = json.loads(cache_for_query_str)
        return item

    # check if the backlog item is in expired backlog
    def expired(self, backlog_id):
        if not self.backlog.get(backlog_id, None):
            if self.expired_backlog.get(backlog_id, None):
                return True

        # check the cache
        cache_for_query_str = cache.get(self.cache_prefix + backlog_id)
        if not cache_for_query_str:
            cache_for_query_str = cache.get(self.cache_expired_prefix + backlog_id)
            if cache_for_query_str:
                return True

        return False

    def expire(self, backlog_id):
        # important: the order of operation should make sure
        # there is at least 1 copy of backlog item in either backlog or expired backlog
        # self.lock.acquire()
        backlogitem = self.backlog.get(backlog_id, None)
        # self.owner.expired_backlog[backlog_id] = backlogitem
        self.expired_backlog[backlog_id] = backlogitem
        self.backlog.pop(backlog_id, None)
        # self.lock.release()

    def remove(self, backlog_id):
        # self.lock.acquire()
        self.backlog.pop(backlog_id, None)
        self.expired_backlog.pop(backlog_id, None)
        cache.delete(self.cache_prefix + backlog_id)
        cache.delete(self.cache_expired_prefix + backlog_id)
        # self.lock.release()

    def reset(self):
        # self.lock.acquire()
        self.backlog.clear()
        self.expired_backlog.clear()
        # self.lock.release()

    #def count(self):
    #    return len(self.backlog)

    class HelperThread(threading.Thread):
        def __init__(self, owner):
            threading.Thread.__init__(self)
            self.daemon = True
            self.duration = 0
            self.owner = owner
            # debug: dump the callstack to determine the callstack, hence the lcm
            # logger.debug("HelperThread __init__ : %s" % traceback.format_exc())

        def run(self):
            logger.debug("Thread %s starts processing backlogs" % self.owner.name)
            nexttimer = 0
            while self.owner.state_ == 1:  # and self.owner.count() > 0:
                if nexttimer > 1000000:
                    # sleep in case of interval > 1 second
                    time.sleep(nexttimer // 1000000)
                nexttimer = 30*1000000  # initial interval in us to be updated:30 seconds
                # logger.debug("self.owner.backlog: %s, len: %s" % (self.owner.name, len(self.owner.backlog)))
                for backlog_id, item in self.owner.backlog.items():
                    # logger.debug("evaluate backlog item: %s" % item)
                    # check interval for repeatable backlog item
                    now = MultiCloudThreadHelper.get_epoch_now_usecond()
                    repeat_interval = item.get("repeat", 0)
                    if repeat_interval > 0:
                        timestamp = item.get("timestamp", 0)
                        timeleft = (now - timestamp
                                              if now > timestamp
                                              else repeat_interval)
                        nexttimer = timeleft if nexttimer > timeleft else nexttimer
                        # compare interval with elapsed time.
                        # workaround the case of timestamp turnaround
                        if repeat_interval > timeleft:
                            # not time to run this backlog item yet
                            continue

                    # logger.debug("process backlog item: %s" % backlog_id)
                    worker = item.get("worker", None)
                    payload = item.get("payload", None)
                    try:
                        item["status"] = worker(*payload) or 0
                    except Exception as e:
                        item["status"] = e.message
                    cache_item_for_query = {
                        "id": item["id"],
                        "status": item["status"]
                    }
                    if item.get("repeat", 0) == 0:
                        self.owner.expire(backlog_id)
                        # keep only the id and status
                        self.owner.expired_backlog[backlog_id] = {"status": item["status"]}

                        #update cache
                        try:
                            cache.set(self.owner.cache_expired_prefix + cache_item_for_query["id"], cache_item_for_query, 3600*24)
                            cache.delete(self.owner.cache_prefix + cache_item_for_query["id"])
                        except Exception as e:
                            logger.error(e.message)
                    else:
                        item["timestamp"] = now
                        #update cache
                        try:
                            cache.set(self.owner.cache_prefix + cache_item_for_query["id"], cache_item_for_query, 3600*24) 
                        except Exception as e:
                            logger.error(e.message)
                pass
            # end of loop
            # while True:
            #     logger.debug("thread sleep for 5 seconds")
            #     time.sleep(5)  # wait forever, testonly
            logger.debug("Thread %s stops processing backlogs" % self.owner.name)
            self.owner.state_ = 0
            # end of processing
