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

from django.db import models

class VimInstModel(models.Model):
    class Meta:
        db_table = 'vim_inst_type_mapping'

    vimid = models.CharField(db_column='VIMID', primary_key=True, max_length=200)
    vimtype = models.CharField(db_column="VIMTYPE", max_length=200)
    viminst_url = models.CharField(db_column="VIMINSTURL", max_length=200)
