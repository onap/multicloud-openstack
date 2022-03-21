# Copyright (c) 2019 Intel Corporation.
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
import platform
import yaml
from logging import config as log_config


CACHE_EXPIRATION_TIME = 3600

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3o-wney!99y)^h3v)0$j16l9=fdjxcb+a8g+q3tfbahcnu2b0o'

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

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
]

ROOT_URLCONF = 'starlingx.urls'

WSGI_APPLICATION = 'starlingx.wsgi.application'

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
MEMCACHED_HOST = os.environ.get('MEMCACHED_HOST', '127.0.0.1')
MEMCACHED_PORT = os.environ.get('MEMCACHED_PORT', '11211')
DEFAULT_CACHE_BACKEND_LOCATION = "%s:%s" % (MEMCACHED_HOST, MEMCACHED_PORT)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': DEFAULT_CACHE_BACKEND_LOCATION,
    }
}

# [RABBITMQ]
RABBITMQ_DEFAULT_USER = os.environ.get('RABBITMQ_DEFAULT_USER', 'guest')
RABBITMQ_DEFAULT_PASS = os.environ.get('RABBITMQ_DEFAULT_PASS', 'guest')
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', '5672')
RABBITMQ_URL = "amqp://%s:%s@%s:%s//" % (
    RABBITMQ_DEFAULT_USER, RABBITMQ_DEFAULT_PASS, RABBITMQ_HOST, RABBITMQ_PORT)

# [MSB]
DEFAULT_MSB_PROTO = "http"
MSB_SERVICE_PROTOCOL = os.environ.get('MSB_PROTO', DEFAULT_MSB_PROTO)
MSB_SERVICE_ADDR = os.environ.get('MSB_ADDR', "127.0.0.1")
MSB_SERVICE_PORT = os.environ.get('MSB_PORT', "80")

# [Multicloud]
MULTICLOUD_PREFIX = "%s://%s:%s/api/multicloud-starlingx/v0" % (
    MSB_SERVICE_PROTOCOL, MSB_SERVICE_ADDR, MSB_SERVICE_PORT)

MULTICLOUD_API_V1_PREFIX = "%s://%s:%s/api/multicloud-starlingx/v1" % (
    MSB_SERVICE_PROTOCOL, MSB_SERVICE_ADDR, MSB_SERVICE_PORT)

# [A&AI]
AAI_ADDR = os.environ.get('AAI_ADDR', "aai.api.simpledemo.openecomp.org")
AAI_PORT = os.environ.get('AAI_PORT', "8443")

AAI_SERVICE_URL = os.environ.get('AAI_SERVICE_URL', "")
if AAI_SERVICE_URL == "":
    AAI_SERVICE_URL = 'https://%s:%s/aai' % (AAI_ADDR, AAI_PORT)

AAI_SCHEMA_VERSION = os.environ.get('AAI_SCHEMA_VERSION', "v13")
AAI_USERNAME = os.environ.get('AAI_USERNAME', "AAI")
AAI_PASSWORD = os.environ.get('AAI_PASSWORD', "AAI")

AAI_BASE_URL = "%s/%s" % (AAI_SERVICE_URL, AAI_SCHEMA_VERSION)

MULTICLOUD_APP_ID = 'MultiCloud-Starlingx'

# [IMAGE LOCAL PATH]
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OPENSTACK_VERSION = "starlingx"
MULTIVIM_VERSION = "multicloud-" + OPENSTACK_VERSION

if platform.system() == 'Windows' or 'test' in sys.argv:
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
            'file_handler': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(BASE_DIR, 'logs/test.log'),
                'formatter': 'standard',
                'maxBytes': 1024 * 1024 * 50,
                'backupCount': 5,
            },
        },

        'loggers': {
            'starlingx': {
                'handlers': ['file_handler'],
                'level': 'DEBUG',
                'propagate': False
            },
            'starlingx_base': {
                'handlers': ['file_handler'],
                'level': 'DEBUG',
                'propagate': False
            },
            'newton_base': {
                'handlers': ['file_handler'],
                'level': 'DEBUG',
                'propagate': False
            },
            'common': {
                'handlers': ['file_handler'],
                'level': 'DEBUG',
                'propagate': False
            },
        }
    }
else:
    log_path = "/var/log/onap/multicloud/openstack/starlingx"
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    LOGGING_CONFIG = None
    # yaml configuration of logging
    LOGGING_FILE = os.path.join(BASE_DIR, 'starlingx/pub/config/log.yml')
    with open(file=LOGGING_FILE, mode='r', encoding="utf-8")as file:
        logging_yaml = yaml.load(stream=file, Loader=yaml.FullLoader)
    log_config.dictConfig(config=logging_yaml)

if 'test' in sys.argv:

    # LOGGING['handlers']['starlingx_handler']['filename'] = 'logs/starlingx.log'

    REST_FRAMEWORK = {}
    import platform

    if platform.system() == 'Linux':
        TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
        TEST_OUTPUT_VERBOSE = True
        TEST_OUTPUT_DESCRIPTIONS = True
        TEST_OUTPUT_DIR = 'test-reports'
