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
import os
import shutil
import logging
import traceback
from six.moves import urllib

logger = logging.getLogger(__name__)


def make_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path, 0777)


def delete_dirs(path):
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error("Failed to delete %s:%s", path, e.message)


def download_file_from_http(url, local_dir, file_name):
    local_file_name = os.path.join(local_dir, file_name)
    is_download_ok = False
    try:
        make_dirs(local_dir)
        req = urllib.request.urlopen(url)
        save_file = open(local_file_name, 'wb')
        save_file.write(req.read())
        save_file.close()
        req.close()
        is_download_ok = True
    except:
        logger.error(traceback.format_exc())
        logger.error("Failed to download %s to %s.", url, local_file_name)
    return is_download_ok, local_file_name
