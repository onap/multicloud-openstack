#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import time

import redis

from django.conf import settings


class SharedLock:
    def __init__(self, lock_key, host=settings.REDIS_HOST,
                 port=settings.REDIS_PORT,
                 password=settings.REDIS_PASSWD, db=9, lock_timeout=5 * 60):
        self.lock_key = lock_key
        self.lock_timeout = lock_timeout
        self.redis = redis.Redis(host=host, port=port, db=db, password=password)
        self.acquire_time = -1

    def acquire(self):
        begin = now = int(time.time())
        while (now - begin) < self.lock_timeout:

            result = self.redis.setnx(self.lock_key, now + self.lock_timeout + 1)
            if result == 1 or result is True:
                self.acquire_time = now
                return True

            current_lock_timestamp = self.redis.get(self.lock_key)
            if not current_lock_timestamp:
                time.sleep(1)
                continue

            current_lock_timestamp = int(current_lock_timestamp)

            if now > current_lock_timestamp:
                next_lock_timestamp = self.redis.getset(self.lock_key, now + self.lock_timeout + 1)
                if not next_lock_timestamp:
                    time.sleep(1)
                    continue
                next_lock_timestamp = int(next_lock_timestamp)

                if next_lock_timestamp == current_lock_timestamp:
                    self.acquire_time = now
                    return True
            else:
                time.sleep(1)
                continue
        return False

    def release(self):
        now = int(time.time())
        if now > self.acquire_time + self.lock_timeout:
            # key expired, do nothing and let other clients handle it
            return
        self.acquire_time = None
        self.redis.delete(self.lock_key)


def do_biz_with_share_lock(lock_name, callback):
    lock = SharedLock(lock_name)
    try:
        if not lock.acquire():
            raise Exception(lock_name + " timeout")
        callback()
    except Exception as e:
        raise e
    finally:
        lock.release()
