# Copyright 2017-2018 Wind River Systems, Inc.
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

import json
import logging
import os
import traceback

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.exceptions import VimDriverNewtonException

logger = logging.getLogger(__name__)


class SwaggerJsonView(APIView):
    def get(self, request):
        json_file = os.path.join(os.path.dirname(__file__), 'multivim.flavor.swagger.json')
        f = open(json_file)
        json_data = json.JSONDecoder().decode(f.read())
        f.close()
        json_file = os.path.join(os.path.dirname(__file__), 'multivim.image.swagger.json')
        f = open(json_file)
        json_data_temp = json.JSONDecoder().decode(f.read())
        f.close()
        json_data["paths"].update(json_data_temp["paths"])
        json_data["definitions"].update(json_data_temp["definitions"])
        json_file = os.path.join(os.path.dirname(__file__), 'multivim.network.swagger.json')
        f = open(json_file)
        json_data_temp = json.JSONDecoder().decode(f.read())
        f.close()
        json_data["paths"].update(json_data_temp["paths"])
        json_data["definitions"].update(json_data_temp["definitions"])
        json_file = os.path.join(os.path.dirname(__file__), 'multivim.subnet.swagger.json')
        f = open(json_file)
        json_data_temp = json.JSONDecoder().decode(f.read())
        f.close()
        json_data["paths"].update(json_data_temp["paths"])
        json_data["definitions"].update(json_data_temp["definitions"])
        json_file = os.path.join(os.path.dirname(__file__), 'multivim.server.swagger.json')
        f = open(json_file)
        json_data_temp = json.JSONDecoder().decode(f.read())
        f.close()
        json_data["paths"].update(json_data_temp["paths"])
        json_data["definitions"].update(json_data_temp["definitions"])
        json_file = os.path.join(os.path.dirname(__file__), 'multivim.volume.swagger.json')
        f = open(json_file)
        json_data_temp = json.JSONDecoder().decode(f.read())
        f.close()
        json_data["paths"].update(json_data_temp["paths"])
        json_data["definitions"].update(json_data_temp["definitions"])
        json_file = os.path.join(os.path.dirname(__file__), 'multivim.vport.swagger.json')
        f = open(json_file)
        json_data_temp = json.JSONDecoder().decode(f.read())
        f.close()
        json_data["paths"].update(json_data_temp["paths"])
        json_data["definitions"].update(json_data_temp["definitions"])
        json_file = os.path.join(os.path.dirname(__file__), 'multivim.tenant.swagger.json')
        f = open(json_file)
        json_data_temp = json.JSONDecoder().decode(f.read())
        f.close()
        json_data["paths"].update(json_data_temp["paths"])
        json_data["definitions"].update(json_data_temp["definitions"])
        json_file = os.path.join(os.path.dirname(__file__), 'multivim.host.swagger.json')
        f = open(json_file)
        json_data_temp = json.JSONDecoder().decode(f.read())
        f.close()
        json_data["paths"].update(json_data_temp["paths"])
        json_data["definitions"].update(json_data_temp["definitions"])
        json_file = os.path.join(os.path.dirname(__file__), 'multivim.limit.swagger.json')
        f = open(json_file)
        json_data_temp = json.JSONDecoder().decode(f.read())
        f.close()
        json_data["paths"].update(json_data_temp["paths"])
        json_data["definitions"].update(json_data_temp["definitions"])

        json_file = os.path.join(os.path.dirname(__file__), 'multicloud.identity.swagger.json')
        f = open(json_file)
        json_data_temp = json.JSONDecoder().decode(f.read())
        f.close()
        json_data["paths"].update(json_data_temp["paths"])

        json_data["basePath"] = "/api/multicloud-newton/v0/"
        json_data["info"]["title"] = "Service NBI of MultiCloud plugin for OpenStack Newton"
        return Response(json_data)

