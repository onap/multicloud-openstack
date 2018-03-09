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

CACHE_EXPIRATION_TIME = 3600

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3o-wney!99y)^h3v)0$j16l9=fdjxcb+a8g+q3tfbahcnu2b0o'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

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
]

ROOT_URLCONF = 'ocata.urls'

WSGI_APPLICATION = 'ocata.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),

    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        # 'rest_framework.parsers.FormParser',
        # 'rest_framework.parsers.FileUploadParser',
    )
}

TIME_ZONE = 'UTC'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s:[%(name)s]:[%(filename)s]-[%(lineno)d] [%(levelname)s]:%(message)s',
        },
    },
    'filters': {
    },
    'handlers': {
        'ocata_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/onap/multicloud/openstack/ocata/ocata.log',
            'formatter': 'standard',
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 5,
        },
    },

    'loggers': {
        'ocata': {
            'handlers': ['ocata_handler'],
            'level': 'DEBUG',
            'propagate': False
        },
        'newton_base': {
            'handlers': ['ocata_handler'],
            'level': 'DEBUG',
            'propagate': False
        },
        'common': {
            'handlers': ['ocata_handler'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# [MSB]
MSB_SERVICE_ADDR = os.environ.get('MSB_ADDR', "127.0.0.1")
MSB_SERVICE_PORT = os.environ.get('MSB_PORT', "80")

#[Multicloud]
MULTICLOUD_PREFIX = "http://%s:%s/api/multicloud-ocata/v0" % (
    MSB_SERVICE_ADDR, MSB_SERVICE_PORT)

# [A&AI]
AAI_ADDR = os.environ.get('AAI_ADDR', "aai.api.simpledemo.openecomp.org")
AAI_PORT = os.environ.get('AAI_PORT', "8443")
AAI_SERVICE_URL = 'https://%s:%s/aai' % (AAI_ADDR, AAI_PORT)
AAI_SCHEMA_VERSION = os.environ.get('AAI_SCHEMA_VERSION', "v11")
AAI_USERNAME = os.environ.get('AAI_USERNAME', "AAI")
AAI_PASSWORD = os.environ.get('AAI_PASSWORD', "AAI")

AAI_BASE_URL = "%s/%s" % (AAI_SERVICE_URL, AAI_SCHEMA_VERSION)

MULTICLOUD_APP_ID = 'MultiCloud-Ocata'

# [IMAGE LOCAL PATH]
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OPENSTACK_VERSION = "ocata"
MULTIVIM_VERSION = "multicloud-" + OPENSTACK_VERSION

if 'test' in sys.argv:

    LOGGING['handlers']['ocata_handler']['filename'] = 'logs/ocata.log'

    REST_FRAMEWORK = {}
    import platform

    if platform.system() == 'Linux':
        TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
        TEST_OUTPUT_VERBOSE = True
        TEST_OUTPUT_DESCRIPTIONS = True
        TEST_OUTPUT_DIR = 'test-reports'
