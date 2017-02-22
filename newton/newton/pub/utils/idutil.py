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
from redisco import containers as cont


def get_auto_id(id_type, id_group="auto_id_hash"):
    auto_id_hash = cont.Hash(id_group)
    auto_id_hash.hincrby(id_type, 1)
    return auto_id_hash.hget(id_type)
