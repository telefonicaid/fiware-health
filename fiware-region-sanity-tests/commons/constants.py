# -*- coding: utf-8 -*-

# Copyright 2015-2016 Telefónica Investigación y Desarrollo, S.A.U
#
# This file is part of FIWARE project.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For those usages not covered by the Apache version 2.0 License please
# contact with opensource@tid.es


# DEFAULTS
DEFAULT_SETTINGS_FILE = 'etc/settings.json'
DEFAULT_LOGGING_CONF = 'etc/logging_sanitychecks.conf'
DEFAULT_PHONEHOME_LOGGING_CONF = 'etc/logging_phonehome.conf'

# LOGGING CONFIGURATION
LOGGING_TEST_LOGGER = "TestCase"
LOGGING_CONF_SECTION_HANDLER = 'sanitychecks_handler_fileHandler'
LOGGING_CONF_SECTION_FORMATTER = 'sanitychecks_formatter_fileFormatter'
LOGGING_OUTPUT_NOVA_CONSOLE_LOG_TEMPLATE = "test_novaconsole_{region_name}_{server_id}.log"

# CONFIGURATION PROPERTIES
PROPERTIES_CONFIG_ENV = "environment"
PROPERTIES_CONFIG_ENV_NAME = "name"
PROPERTIES_CONFIG_CRED = "credentials"
PROPERTIES_CONFIG_CRED_KEYSTONE_URL = "keystone_url"
PROPERTIES_CONFIG_CRED_TENANT_ID = "tenant_id"
PROPERTIES_CONFIG_CRED_TENANT_NAME = "tenant_name"
PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME = "user_domain_name"
PROPERTIES_CONFIG_CRED_PROJECT_DOMAIN_NAME = "project_domain_name"
PROPERTIES_CONFIG_CRED_USER_ID = "user_id"
PROPERTIES_CONFIG_CRED_USERNAME = "username"
PROPERTIES_CONFIG_CRED_PASSWORD = "password"
PROPERTIES_CONFIG_TEST = "test_configuration"
PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT = "phonehome_endpoint"
PROPERTIES_CONFIG_REGION = "region_configuration"
PROPERTIES_CONFIG_REGION_EXTERNAL_NET = "external_network_name"
PROPERTIES_CONFIG_REGION_SHARED_NET = "shared_network_name"
PROPERTIES_CONFIG_REGION_TEST_FLAVOR = "test_flavor"
PROPERTIES_CONFIG_REGION_TEST_IMAGE = "test_image"
PROPERTIES_CONFIG_REGION_TEST_LOGIN_NAME = "test_login_name"
PROPERTIES_CONFIG_KEY_TEST_CASES = "key_test_cases"
PROPERTIES_CONFIG_OPT_TEST_CASES = "opt_test_cases"
PROPERTIES_CONFIG_GLANCE = "glance_configuration"
PROPERTIES_CONFIG_GLANCE_IMAGES = "required_images"
PROPERTIES_CONFIG_SWIFT = "swift_configuration"
PROPERTIES_CONFIG_SWIFT_BIG_FILE_1 = "big_file_url_1"
PROPERTIES_CONFIG_SWIFT_BIG_FILE_2 = "big_file_url_2"
PROPERTIES_CONFIG_SWIFT_ENABLED = "test_object_storage"
PROPERTIES_CONFIG_METADATA_SERVICE_URL = "openstack_metadata_service_url"

# TASK TIMERS AND TIMEOUTS (in seconds)
DEFAULT_REQUEST_TIMEOUT = 60
MAX_WAIT_ITERATIONS = 60
MAX_WAIT_SSH_CONNECT_ITERATIONS = 35
MAX_CIDR_SUBNET_ITERATIONS = 5
OBJECT_STORE_MAX_RETRIES = 2
SLEEP_TIME = 5

# TEST DATA
DEFAULT_DNS_SERVER = "8.8.8.8"
TEST_FLAVOR_DEFAULT = "small"
TEST_IMAGE_DEFAULT = "base_centos_6"
TEST_LOGIN_NAME_DEFAULT = "centos"
TEST_SHARED_NET_DEFAULT = "shared-net"
TEST_CIDR_PATTERN = "10.250.%d.0/24"
TEST_CIDR_DEFAULT = TEST_CIDR_PATTERN % 254
TEST_CIDR_RANGE = xrange(128, 254)
TEST_SEC_GROUP_PREFIX = "testing_sec_group"
TEST_KEYPAIR_PREFIX = "testing_keypair"
TEST_SERVER_PREFIX = "testing_instance"
TEST_NETWORK_PREFIX = "testing_network"
TEST_ROUTER_PREFIX = "testing_router"
TEST_CONTAINER_PREFIX = "testing_container"
TEST_TEXT_OBJECT_PREFIX = "_testing_text_object"
TEST_BIG_OBJECT_PREFIX = "_test_big_file"
TEST_BIG_OBJECT_REMOTE_PREFIX = "_remote_"
TEST_TEXT_FILE_EXTENSION = ".txt"
TEST_BIG_FILE_EXTENSION = ".zip"

# SWIFT CONSTANTS
SWIFT_RESOURCES_PATH = "resources/swift_objects/"
SWIFT_TMP_RESOURCES_PATH = "/tmp/swift_objects/"

# SSH CONNECTION (timeouts in seconds)
SSH_CONNECTION_PORT = 22
SSH_CONNECTION_TIMEOUT = 8

# PHONEHOME SERVER (timeouts in seconds)
PHONEHOME_USERDATA_PATH = "resources/templates/userdata/test.snat.phonehome.template"
PHONEHOME_USERDATA_METADATA_PATH = "resources/templates/userdata/test.meta.phonehome.template"
PHONEHOME_TIMEOUT = 175
PHONEHOME_DBUS_NAME = "org.fiware.fihealth"
PHONEHOME_DBUS_OBJECT_PATH = "/phonehome"
PHONEHOME_DBUS_OBJECT_METADATA_PATH = "/metadata"
PHONEHOME_SIGNAL = "phonehome_signal"
PHONEHOME_METADATA_SIGNAL = "phonehome_metadata_signal"
PHONEHOME_TX_ID_HEADER = "TransactionId"

# SERVICES NAMES
SERVICE_SWIFT_NAME = "object-store"

# ENDPOINTS
ENDPOINT_TYPE_PUBLIC_URL = "publicURL"
