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

import os
import sys

from logging import config
from onaplogging import monkey
monkey.patch_all()


CACHE_EXPIRATION_TIME = 3600

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3o-wney!99y)^h3v)0$j16l9=fdjxcb+a8g+q3tfbahcnu2b0o'

# SECURITY WARNING: don't run with debug turned on in production!
#DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'titanium_cloud.middleware.LogContextMiddleware',
]

ROOT_URLCONF = 'titanium_cloud.urls'

WSGI_APPLICATION = 'titanium_cloud.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),

    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    )
}

TIME_ZONE = 'UTC'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'


DEFAULT_MSB_ADDR = "127.0.0.1"
DEFAULT_CACHE_BACKEND_LOCATION = '127.0.0.1:11211'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': DEFAULT_CACHE_BACKEND_LOCATION,
    }
}

# [MSB]
MSB_SERVICE_ADDR = os.environ.get('MSB_ADDR', DEFAULT_MSB_ADDR)
MSB_SERVICE_PORT = os.environ.get('MSB_PORT', "80")

#[Multicloud]
MULTICLOUD_PREFIX = "http://%s:%s/api/multicloud-titanium_cloud/v0" % (
    MSB_SERVICE_ADDR, MSB_SERVICE_PORT)

# [A&AI]
AAI_ADDR = os.environ.get('AAI_ADDR', "aai.api.simpledemo.openecomp.org")
AAI_PORT = os.environ.get('AAI_PORT', "8443")
AAI_SERVICE_URL = 'https://%s:%s/aai' % (AAI_ADDR, AAI_PORT)
AAI_SCHEMA_VERSION = os.environ.get('AAI_SCHEMA_VERSION', "v11")
AAI_USERNAME = os.environ.get('AAI_USERNAME', "AAI")
AAI_PASSWORD = os.environ.get('AAI_PASSWORD', "AAI")

AAI_BASE_URL = "%s/%s" % (AAI_SERVICE_URL, AAI_SCHEMA_VERSION)

MULTICLOUD_APP_ID = 'MultiCloud-Titanium_Cloud'

# [IMAGE LOCAL PATH]
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OPENSTACK_VERSION = "titanium_cloud"
MULTIVIM_VERSION = "multicloud-" + OPENSTACK_VERSION


LOGGING_CONFIG = None
# yaml configuration of logging
LOGGING_FILE = os.path.join(BASE_DIR, 'titanium_cloud/pub/config/log.yml')
config.yamlConfig(filepath=LOGGING_FILE, watchDog=True)

if 'test' in sys.argv:

    #LOGGING['handlers']['titanium_cloud_handler']['filename'] = 'logs/titanium_cloud.log'

    REST_FRAMEWORK = {}
    import platform

    if platform.system() == 'Linux':
        TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
        TEST_OUTPUT_VERBOSE = True
        TEST_OUTPUT_DESCRIPTIONS = True
        TEST_OUTPUT_DIR = 'test-reports'
