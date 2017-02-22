# Copyright (c) 2017 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import logging

from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class SampleList(APIView):
    """
    List all samples.
    """
    def get(self, request, format=None):
        logger.debug("get")
        return Response({"status": "active"})
