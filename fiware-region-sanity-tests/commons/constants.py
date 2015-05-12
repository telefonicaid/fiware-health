# -*- coding: utf-8 -*-

# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U
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


# LOGGING CONFIGURATION
LOGGING_FILE = "resources/logging.conf"

# CONFIGURATION PROPERTIES
PROPERTIES_FILE = "resources/settings.json"
PROPERTIES_LOGGER = "TestCase"
PROPERTIES_CONFIG_ENV = "environment"
PROPERTIES_CONFIG_ENV_NAME = "name"
PROPERTIES_CONFIG_CRED = "credentials"
PROPERTIES_CONFIG_CRED_KEYSTONE_URL = "keystone_url"
PROPERTIES_CONFIG_CRED_TENANT_ID = "tenant_id"
PROPERTIES_CONFIG_CRED_TENANT_NAME = "tenant_name"
PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME = "user_domain_name"
PROPERTIES_CONFIG_CRED_USER = "user"
PROPERTIES_CONFIG_CRED_PASS = "password"
PROPERTIES_CONFIG_TEST = "test_configuration"
PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT = "phonehome_endpoint"
PROPERTIES_CONFIG_REGION = "region_configuration"
PROPERTIES_CONFIG_REGION_EXTERNAL_NET = "external_network_name"
PROPERTIES_CONFIG_REGION_TEST_FLAVOR = "test_flavor"
PROPERTIES_CONFIG_KEYTESTCASES = "key_test_cases"

# TASK TIMERS AND TIMEOUTS
DEFAULT_REQUEST_TIMEOUT = 60
MAX_WAIT_ITERATIONS = 60
MAX_WAIT_SSH_CONNECT_ITERATIONS = 35
SLEEP_TIME = 5
OBJECT_STORE_MAX_RETRIES = 2

# TEST DATA
BASE_IMAGE_NAME = "CentOS-6.3init"
DEFAULT_DNS_SERVER = "8.8.8.8"
TEST_FLAVOR_DEFAULT = "small"
TEST_CIDR_PATTERN = "10.250.%d.0/24"
TEST_CIDR_DEFAULT = TEST_CIDR_PATTERN % 0
TEST_SEC_GROUP_PREFIX = "testing_sec_group"
TEST_KEYPAIR_PREFIX = "testing_keypair"
TEST_SERVER_PREFIX = "testing_instance"
TEST_NETWORK_PREFIX = "testing_network"
TEST_ROUTER_PREFIX = "testing_router"
TEST_CONTAINER_PREFIX = "testing_container"

# SSH CONNECTION (reference to time, in seconds)
SSH_CONNECTION_PORT = 22
SSH_CONNECTION_TIMEOUT = 8

# PHONEHOME SERVER (time in seconds)
PHONEHOME_USERDATA_PATH = "resources/templates/userdata/test.snat.phonehome.template"
PHONEHOME_TIMEOUT = 175
PHONEHOME_DBUS_NAME = "org.fiware.fihealth"
PHONEHOME_DBUS_OBJECT_PATH = "/phonehome"
PHONEHOME_SIGNAL = "phonehome_signal"

# SERVICES NAMES
SERVICE_SWIFT_NAME = "object-store"
ENDPOINT_TYPE_PUBLIC_URL = "publicURL"
