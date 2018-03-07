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

import json
import logging
import os
import traceback

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import VimDriverNewtonException
from newton_base.swagger import views as newton_json_view

logger = logging.getLogger(__name__)


class SwaggerJsonView(newton_json_view.SwaggerJsonView):

    def get(self, request):
        '''
        reuse newton code and update the basePath
        :param request:
        :return:
        '''

        resp = super(SwaggerJsonView,self).get(request)
        json_data = resp.data if resp else None
        if json_data:
            json_data["basePath"] = "/api/multicloud-ocata/v0/"
            json_data["info"]["title"] = "Service NBI of MultiCloud plugin for OpenStack Ocata"
            return Response(data=json_data, status=200)
        else:
            return Response(data={'error':'internal error'}, status=500)


