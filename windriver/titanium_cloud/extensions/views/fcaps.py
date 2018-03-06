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
import traceback
import threading

from django.core.cache import cache

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from titanium_cloud.pub.config import config
from newton.pub.exceptions import VimDriverNewtonException
from newton.requests.views.util import VimDriverUtils
from newton.pub.msapi import extsys



#from newton.extensions.views import fcaps as newton_fcaps

logger = logging.getLogger(__name__)

DEBUG=True

#dict to store running worker threads
running_threads = {}
running_thread_lock = threading.Lock()

class GuestMonitorWorker (threading.Thread):
    service = {'service_type': 'platform',
               'interface': 'public'}
    def __init__(self, vimid, tenantid=None):
        threading.Thread.__init__(self)
        self.vimid = vimid
        self.tenantid = tenantid
        self.eventid = '700.213' #Guest Heartbeat failed for instance

    def run(self):
        logger.debug("start GuestMonitorWorker %s,%s" % (self.vimid, self.tenantid))

        viminfo = VimDriverUtils.get_vim_info(self.vimid)
        sess = VimDriverUtils.get_session(viminfo, tenantid=self.tenantid)

        thread_info = running_threads.get(self.vimid)
        if not thread_info:
            return

        while thread_info.get('state') == 'start':
            #wait for jobs
            vservers = thread_info.get('vservers') if thread_info else None
            if not vservers:
                continue

            # do jobs
            for (vserverid, vserverinfo) in vservers.items():
                status_code, heartbeat_event = \
                    self.monitor_heartbeat(self.vimid, self.tenantid, vserverid, viminfo, sess)

                if status_code == status.HTTP_403_FORBIDDEN:
                    #invalid tenant, so remove this job

                    running_thread_lock.acquire()
                    thread_info['state'] = 'error'
                    running_thread_lock.release()

                    return #exit this thread since error

                if heartbeat_event:
                    #report to VES
                    #tbd
                    pass
                else:
                    continue

        running_thread_lock.acquire()
        thread_info['state'] = 'stopped'
        running_thread_lock.release()

        logger.debug("stop GuestMonitorWorker %s, %s, %s" % (self.vimid, self.tenantid, self.vserverid))
#        running_thread_lock.acquire()
#        running_threads.pop(self.vimid)
#        running_thread_lock.release()

    def monitor_heartbeat(self, vimid, tenantid, vserverid, viminfo, session):
        logger.debug("GuestMonitorWorker--monitor_heartbeat::> %s" % (vserverid))
        try:
            # prepare request resource to vim instance
            req_resouce = "/v1/event_log?q.field=entity_instance_id&\
                q.field=event_log_id&\
                q.op=eq&q.op=eq&q.type=&q.type=&\
                q.value=tenant\%%s.instance\%%s&\
                q.value=%s" % (tenantid, vserverid, self.eventid)

            resp = session.get(req_resouce, endpoint_filter=self.service,
                    headers={"Content-Type": "application/json",
                             "Accept": "application/json"})

            logger.debug("response status code of monitor_heartbeat %s" % resp.status_code)

            return resp.status_code, resp.json() if resp.content else None

        except HttpError as e:
            logger.error("monitor_heartbeat, HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return e.http_status, e.response.json()
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error("Failed to monitor_heartbeat:%s" % str(e))
            return e.http_status, e.response.json()


class GuestMonitor(APIView):

    def __init__(self):
        self.proxy_prefix = config.MULTICLOUD_PREFIX
        self._logger = logger

    def post(self, request, vimid="", vserverid=""):
        '''Start guest monitoring on specified virtual server'''
        self._logger.debug("GuestMonitor--post::data> %s" % request.data)
        self._logger.debug("GuestMonitor--post::vimid > %s" % vimid)

        try:
            # populate proxy identity url
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)

            tenant_name = request.data.get('tenantName')
            tenant_id = request.data.get('tenantID')
            ves_url = request.data.get('vesurl')

            # prepare request resource to vim instance
            # get token:
            viminfo = VimDriverUtils.get_vim_info(vimid)
            # the tenant should have the privilege to access the event-log API
            # usually it is 'admin'. Otherwise the 403 will be returned.
            sess = None
            if tenant_id:
                sess = VimDriverUtils.get_session(viminfo, tenantid=tenant_id)
            else:
                sess = VimDriverUtils.get_session(viminfo, tenantname=tenant_name)

            #now try to convert tenant_name to tenant_id
            #tbd

            thread_info = running_threads[vimid]

            if thread_info and  thread_info['state'] == 'error':
                #the thread is in error state, so recreate with new tenant_id
                running_thread_lock.acquire()
                running_threads.pop(vimid)
                running_thread_lock.release()
                thread_info = None

            if not thread_info:
                tmp_thread = GuestMonitorWorker(vimid, tenant_id)
                if not tmp_thread:
                    raise VimDriverNewtonException(message="internal error",
                                               content="Fail to spawn thread for Guest Monitoring",
                                               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
                thread_info = {
                    'thread': tmp_thread,
                    'tenantid':tenant_id,
                    'vservers':{},
                    'state':'start'
                }

                running_thread_lock.acquire()
                running_threads[vimid] = thread_info
                running_thread_lock.release()
                tmp_thread.start()
            else:
                thread_info['state'] = 'start'


            vservers = thread_info.get('vservers')
            vservers[vserverid] = {'vesurl': ves_url}

            return Response(status=status.HTTP_202_ACCEPTED)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def GET(self, request, vimid="", vserverid=""):
        '''query guest monitoring on specified virtual server'''
        self._logger.debug("GuestMonitor--get::data> %s" % request.data)
        self._logger.debug("GuestMonitor--get::vimid > %s" % vimid)

        try:
            # populate proxy identity url
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)

            tenant_name = request.data.get('tenantName')
            tenant_id = request.data.get('tenantID')
            vserver_id = vserverid

            # prepare request resource to vim instance
            # get token:
            viminfo = VimDriverUtils.get_vim_info(vimid)
            # the tenant should have the privilege to access the event-log API
            # usually it is 'admin'. Otherwise the 403 will be returned.
            sess = None
            if tenant_id:
                sess = VimDriverUtils.get_session(viminfo, tenantid=tenant_id)
            else:
                sess = VimDriverUtils.get_session(viminfo, tenantname=tenant_name)

            #now try to convert tenant_name to tenant_id, and vserver_name to vserver_id
            #tbd

            thread_info = running_threads[vimid]
            if not thread_info \
                    or not thread_info.get('vservers') \
                    or not thread_info.get('vservers').get(vserverid):
                status_code = status.HTTP_204_NO_CONTENT
                content = {'error':
                               'Guest Monitor job is not created for this virtual server,\
                               vim id: %s, vserver id: %s'
                               % (self.vimid,  vserverid)}
                pass
            elif thread_info['state'] == 'error':
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                content = {'error':
                               'Guest Monitor job for this virtual server \
                               (vim id: %s, vserver id: %s) failed due to: %s'
                               % (self.vimid,  vserverid, thread_info.get('message'))}
                pass
            else:
                vserverinfo = thread_info.get('vservers').get(vserverid)
                content = vserverinfo.get('message')
                status_code = vserverinfo.get('status') or status.HTTP_200_OK
                pass

            #return Response(status=status.HTTP_202_ACCEPTED)
            return Response(status=status_code, data=content)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    def DELETE(self, request, vimid="", vserverid=""):
        '''Stop guest monitoring on specified virtual server'''
        self._logger.debug("GuestMonitor--delete::data> %s" % request.data)
        self._logger.debug("GuestMonitor--delete::vimid > %s" % vimid)

        try:
            # populate proxy identity url
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)

            tenant_name = request.data.get('tenantName')
            tenant_id = request.data.get('tenantID')

            # prepare request resource to vim instance
            # get token:
            viminfo = VimDriverUtils.get_vim_info(vimid)
            # the tenant should have the privilege to access the event-log API
            # usually it is 'admin'. Otherwise the 403 will be returned.
            sess = None
            if tenant_id:
                sess = VimDriverUtils.get_session(viminfo, tenantid=tenant_id)
            else:
                sess = VimDriverUtils.get_session(viminfo, tenantname=tenant_name)

            #now try to convert tenant_name to tenant_id, and vserver_name to vserver_id
            #tbd

            thread_info = running_threads[vimid]
            if not thread_info:
                status_code = status.HTTP_204_NO_CONTENT
            else:
                vservers = thread_info.get('vservers')
                if vservers.get(vserverid):
                    vservers.pop(vserverid)

                running_thread_lock.acquire()
                if len(vservers.items()) == 0:
                    thread_info.stop()
                    running_threads.pop(vimid)
                running_thread_lock.release()
                status_code = status.HTTP_202_ACCEPTED

            return Response(status=status_code)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
