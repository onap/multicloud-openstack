# Copyright (c) 2017 Wind River Systems, Inc.
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

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.exceptions import VimDriverNewtonException

from util import VimDriverUtils

logger = logging.getLogger(__name__)


class Flavors(APIView):
    service = {'service_type': 'compute',
               'interface': 'public',
               'region_name': 'RegionOne'}
    keys_mapping = [
        ("project_id", "tenantId"),
        ("ram", "memory"),
        ("vcpus", "vcpu"),
        ("OS-FLV-EXT-DATA:ephemeral", "ephemeral"),
        ("os-flavor-access:is_public", "isPublic"),
        ("extra_specs", "extraSpecs"),
    ]

    def convertExtraSpecs(self, extraSpecs, extra_specs, reverse=False):
       if reverse == False:
          #from extraSpecs to extra_specs
          for spec in extraSpecs:
              extra_specs[spec['keyName']] = spec['value']
       else:
          for k,v in extra_specs.items():
              spec={}
              spec['keyName']=k
              spec['value']=v
              extraSpecs.append(spec)
    pass

    def get(self, request, vimid="", tenantid="", flavorid=""):
        logger.debug("Flavors--get::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            resp = self.get_flavor(sess, request, flavorid)
            content = resp.json()

            if flavorid:
                flavor = content.pop("flavor", None)
                extraResp = self.get_flavor_extra_specs(sess, flavor["id"])
                extraContent = extraResp.json()
                if extraContent["extra_specs"]:
                    extraSpecs = []
                    self.convertExtraSpecs(extraSpecs, extraContent["extra_specs"], True)
                    flavor["extraSpecs"] = extraSpecs
                VimDriverUtils.replace_key_by_mapping(flavor,
                                                   self.keys_mapping)
                content.update(flavor)

            else:
                wanted = None
                #check if query contains name="flavorname"
                if query:
                    for queryone in query.split('&'):
                        k,v = queryone.split('=')
                        if k == "name":
                            wanted = v
                            break
                        pass

                if wanted:
                   oldFlavors = content.pop("flavors", None)
                   content["flavors"] = []
                   for flavor in oldFlavors:
                       if wanted == flavor["name"]:
                           content["flavors"].append(flavor)
                       pass


                #iterate each flavor to get extra_specs
                for flavor in content["flavors"]:
                    extraResp = self.get_flavor_extra_specs(sess, flavor["id"])
                    extraContent = extraResp.json()
                    if extraContent["extra_specs"]:
                        extraSpecs = []
                        self.convertExtraSpecs(extraSpecs, extraContent["extra_specs"], True)
                        flavor["extraSpecs"] = extraSpecs
                    VimDriverUtils.replace_key_by_mapping(flavor,
                                                   self.keys_mapping)

            #add extra keys
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
            }
            content.update(vim_dict)


            return Response(data=content, status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass

    def get_flavor_extra_specs(self, sess, flavorid):
        if not flavorid:
            return {}
        else:
            logger.debug("Flavors--get_extra_specs::> %s" % flavorid)
            # prepare request resource to vim instance
            req_resouce = "/flavors/%s/os-extra_specs" % flavorid

            resp = sess.get(req_resouce, endpoint_filter=self.service)
            return resp
        pass

    def get_flavor(self, sess, request, flavorid=""):
        logger.debug("Flavors--get basic")
        if not sess:
            return {}
        else:
            # prepare request resource to vim instance
            req_resouce = "/flavors"
            if flavorid:
                req_resouce += "/%s" % flavorid
            else:
                req_resouce += "/detail"

            query = VimDriverUtils.get_query_part(request)
            if query:
                req_resouce += "?%s" % query

            resp = sess.get(req_resouce, endpoint_filter=self.service)
            return resp
        pass


    def post(self, request, vimid="", tenantid="", flavorid=""):
        logger.debug("Flavors--post::> %s" % request.data)
        sess = None
        resp = None
        resp_body = None
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            #check if the flavor is already created: name or id
            tmpresp = self.get_flavor(sess, request)
            content = tmpresp.json()
            #iterate each flavor to get extra_specs
            existed = False
            for flavor in content["flavors"]:
                if flavor["name"] == request.data["name"]:
                   existed = True
                   break
                elif hasattr(request.data, "id") and flavor["id"] == request.data["id"]:
                   existed = True
                   break
                pass

            if existed == True:
                extraResp = self.get_flavor_extra_specs(sess, flavor["id"])
                extraContent = extraResp.json()
                if extraContent["extra_specs"]:
                    extraSpecs = []
                    self.convertExtraSpecs(extraSpecs, extraContent["extra_specs"], True)
                    flavor["extraSpecs"] = extraSpecs
                VimDriverUtils.replace_key_by_mapping(flavor,
                                               self.keys_mapping)
                vim_dict = {
                    "vimName": vim["name"],
                    "vimId": vim["vimId"],
                    "tenantId": tenantid,
                     "returnCode": 0,
                }
                flavor.update(vim_dict)
                return Response(data=flavor, status=tmpresp.status_code)

            extraSpecs = request.data.pop("extraSpecs", None)
            #create flavor first
            resp = self.create_flavor(sess, request)
            if resp.status_code == 200:
                resp_body = resp.json()["flavor"]
            else:
                return resp


            flavorid = resp_body['id']
            if extraSpecs:
                extra_specs={}
                self.convertExtraSpecs(extraSpecs, extra_specs, False)
#                logger.debug("extraSpecs:%s" % extraSpecs)
#                logger.debug("extra_specs:%s" % extra_specs)
                extraResp = self.create_flavor_extra_specs(sess, extra_specs, flavorid)
                if extraResp.status_code == 200:
                    #combine the response body and return
                    tmpSpecs = []
                    tmpRespBody = extraResp.json()
                    self.convertExtraSpecs(tmpSpecs, tmpRespBody['extra_specs'], True)

                    resp_body.update({"extraSpecs":tmpSpecs})
                else:
                    #rollback
                    delete_flavor(self, request, vimid, tenantid, flavorid)
                    return extraResp

            VimDriverUtils.replace_key_by_mapping(resp_body, self.keys_mapping)
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
                 "returnCode": 1,
            }
            resp_body.update(vim_dict)
            return Response(data=resp_body, status=resp.status_code)
        except VimDriverNewtonException as e:
            if sess and resp and resp.status_code == 200:
                self.delete_flavor(sess, flavorid)

            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            logger.error(traceback.format_exc())

            if sess and resp and resp.status_code == 200:
                self.delete_flavor(sess, flavorid)

            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass


    def create_flavor(self, sess, request):
        logger.debug("Flavors--create::> %s" % request.data)
        # prepare request resource to vim instance
        req_resouce = "/flavors"

        flavor = request.data

        VimDriverUtils.replace_key_by_mapping(flavor,
                                              self.keys_mapping, True)
        req_body = json.JSONEncoder().encode({"flavor": flavor})
        return sess.post(req_resouce, data=req_body,
                         endpoint_filter=self.service)
        pass



    def create_flavor_extra_specs(self, sess, extraspecs, flavorid):
        logger.debug("Flavors extra_specs--post::> %s" % extraspecs)
        # prepare request resource to vim instance
        req_resouce = "/flavors"
        if flavorid:
            req_resouce += "/%s/os-extra_specs" % flavorid
        else:
            raise VimDriverNewtonException(message="VIM newton exception",
                       content="internal bug in creating flavor extra specs",
                       status_code=500)

        req_body = json.JSONEncoder().encode({"extra_specs": extraspecs})

        return sess.post(req_resouce, data=req_body,
                         endpoint_filter=self.service)
        pass





    def delete(self, request, vimid="", tenantid="", flavorid=""):
        logger.debug("Flavors--delete::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            #delete extra specs one by one
            resp = self.delete_flavor_extra_specs(sess, flavorid)

            #delete flavor
            resp = self.delete_flavor(sess, flavorid)

            #return results
            return Response(status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass


    def delete_flavor_extra_specs(self, sess, flavorid):
        logger.debug("Flavors--delete extra::> %s" % flavorid)

        #delete extra specs one by one
        resp = self.get_flavor_extra_specs(sess, flavorid)
        extra_specs = resp.json()
        if extra_specs and extra_specs["extra_specs"]:
            for k, _ in extra_specs["extra_specs"].items():
                self.delete_flavor_one_extra_spec(sess, flavorid, k)
        return resp
        pass

    def delete_flavor_one_extra_spec(self, sess, flavorid, extra_spec_key):
        logger.debug("Flavors--delete  1 extra::> %s" % extra_spec_key)
        # prepare request resource to vim instance
        req_resouce = "/flavors"
        if flavorid and extra_spec_key:
            req_resouce += "/%s" % flavorid
            req_resouce += "/os-extra_specs/%s" % extra_spec_key
        else:
            raise VimDriverNewtonException(message="VIM newton exception",
                   content="internal bug in deleting flavor extra specs: %s" % extra_spec_key,
                   status_code=500)

        resp = sess.delete(req_resouce, endpoint_filter=self.service)
        return resp
        pass


    def delete_flavor(self, sess, flavorid):
        logger.debug("Flavors--delete basic::> %s" % flavorid)
        # prepare request resource to vim instance
        req_resouce = "/flavors"
        if flavorid:
            req_resouce += "/%s" % flavorid
        else:
            raise VimDriverNewtonException(message="VIM newton exception",
                   content="internal bug in deleting flavor",
                   status_code=500)

        resp = sess.delete(req_resouce, endpoint_filter=self.service)
        return resp
        pass

