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
from django.core.cache import cache

logger = logging.getLogger(__name__)

# note: memcached key length should be < 250, the value < 1MB

def flush_cache_by_url(resource_url):
    try:
        cache.delete("AAI_" + resource_url)
    except:
        pass # silently drop any exception


def get_cache_by_url(resource_url):
    try:
        if filter_cache_by_url(resource_url):
            value = cache.get("AAI_" + resource_url)
            # logger.debug("Find cache the resource: %s, %s" %( resource_url, value))
            return json.loads(value) if value else None
        else:
            return None
    except Exception as e:
        logger.error("get_cache_by_url exception: %s" % e.message)
        return None


def set_cache_by_url(resource_url, resource_in_json):
    try:
        # filter out unmanaged AAI resource
        if filter_cache_by_url(resource_url):
            # cache the resource for 24 hours
            # logger.debug("Cache the resource: "+ resource_url)
            cache.set("AAI_" + resource_url, json.dumps(resource_in_json), 3600 * 24)
    except Exception as e:
        logger.error("get_cache_by_url exception: %s" % e.message)
        pass

def filter_cache_by_url(resource_url):
    # hardcoded filter: cloud region only
    if resource_url.find(r"cloud-infrastructure/cloud-regions/cloud-region") > 0:
        return True
    else:
        return False