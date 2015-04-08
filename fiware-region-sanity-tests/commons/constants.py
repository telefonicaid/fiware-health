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

__author__ = 'jfernandez'


# CONFIGURATION PROPERTIES
PROPERTIES_FILE = "resources/settings.json"
PROPERTIES_CONFIG_ENV = "environment"
PROPERTIES_CONFIG_ENV_NAME = "name"
PROPERTIES_CONFIG_CRED = "credentials"
PROPERTIES_CONFIG_CRED_KEYSTONE_URL = "keystone_url"
PROPERTIES_CONFIG_CRED_TENANT_ID = "tenant_id"
PROPERTIES_CONFIG_CRED_TENANT_NAME = "tenant_name"
PROPERTIES_CONFIG_CRED_USER = "user"
PROPERTIES_CONFIG_CRED_PASS = "password"
PROPERTIES_CONFIG_REGION_CONFIG = "region_configuration"
PROPERTIES_CONFIG_REGION_CONFIG_EXTERNAL_NET = "external_network_name"
PROPERTIES_CONFIG_KEYTESTCASES = "key_test_cases"

# TASK TIMERS AND TIMEOUTS
DEFAULT_REQUEST_TIMEOUT = 60
WAIT_FOR_INSTANCE_ACTIVE = 60
SLEEP_TIME = 5

# TEST DATA
BASE_IMAGE_NAME = "CentOS-6.3init"
TEST_SEC_GROUP = "testing_sec_group"
