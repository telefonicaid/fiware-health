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


from keystoneclient import auth, session
from keystoneclient.openstack.common.apiclient.exceptions import ClientException
from commons.nova_operations import FiwareNovaOperations
from commons.neutron_operations import FiwareNeutronOperations
from commons.constants import *
import unittest
import logging
import json


class FiwareTestCase(unittest.TestCase):

    # Test region (to be overriden)
    region_name = None

    # Test authentication
    auth_url = None
    auth_sess = None
    auth_token = None

    # Temporal test data
    test_world = dict()

    # Test logger
    logger = None

    @classmethod
    def load_project_properties(cls):
        """
        Parse the JSON configuration file located in the settings folder and
        store the resulting dictionary in the config class variable.
        """

        cls.logger.debug("Loading test settings...")
        with open(PROPERTIES_FILE) as config_file:
            try:
                cls.conf = json.load(config_file)
            except Exception as e:
                assert False, "Error parsing config file '{}': {}".format(PROPERTIES_FILE, e)

        for name in [PROPERTIES_CONFIG_CRED_USER, PROPERTIES_CONFIG_CRED_PASS, PROPERTIES_CONFIG_CRED_TENANT_ID]:
            if not cls.conf[PROPERTIES_CONFIG_CRED][name]:
                assert False, "A value for '{}' must be provided".format(name)

    @classmethod
    def init_auth(cls):
        """
        Init the variables related to authorization, needed to execute tests
        """

        credentials = auth.identity.v2.Password(
            auth_url=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_KEYSTONE_URL],
            username=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_USER],
            password=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_PASS],
            tenant_name=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID])

        cls.logger.debug("Getting auth token...")
        cls.auth_url = credentials.auth_url
        cls.auth_sess = session.Session(auth=credentials)
        try:
            cls.auth_token = cls.auth_sess.get_token()
            cls.logger.debug("X-Auth-Token: %s", cls.auth_token)
        except ClientException as e:
            cls.logger.error("No auth token (%s): all tests will be skipped", e.message)

    @classmethod
    def init_world(cls):
        """
        Init the 'test_world' variable to store created data by tests
        """

        cls.test_world.update({
            'servers': list(),
            'sec_groups': list(),
            'keypair_names': list(),
            'networks': list(),
            'routers': list(),
            'allocated_ips': list()
        })

    @classmethod
    def setUpClass(cls):
        """
        Setup testcase (executed before ALL tests): initialize logger and REST-Clients.
        """

        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        cls.logger = logging.getLogger("TestCase")
        cls.logger.addHandler(handler)
        cls.logger.setLevel(logging.NOTSET)

        # These tests should be particularized for a region
        cls.logger.debug("Tests for '%s' region", cls.region_name)

        # Load properties from config file
        cls.load_project_properties()
        username = cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_USER]
        tenant_id = cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID]
        cls.logger.debug("Settings = { user: '%s', tenant: '%s' }", username, tenant_id)

        # Initialize session and try to get auth token
        cls.init_auth()

        # Initialize world variables
        cls.init_world()

        # Initialize OpenStack operations
        cls.nova_operations = FiwareNovaOperations(cls.logger, cls.region_name, auth_session=cls.auth_sess)
        cls.neutron_operations = FiwareNeutronOperations(cls.logger, cls.region_name, tenant_id,
                                                         auth_session=cls.auth_sess)

    @classmethod
    def tearDownClass(cls):
        None

    def setUp(self):
        """
        Skip test if no auth token could be retrieved.
        """
        if not self.auth_token:
            self.skipTest("No auth token could be retrieved")
