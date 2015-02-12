# -*- coding: utf-8 -*-

# Copyright 2015 Telefonica Investigación y Desarrollo, S.A.U
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


from commons.nova_operations import FiwareNovaOperations
from commons.neutron_operations import FiwareNeutronOperations
import unittest
from commons.constants import PROPERTIES_FILE, PROPERTIES_CONFIG_CRED, PROPERTIES_CONFIG_CRED_PASS, \
    PROPERTIES_CONFIG_CRED_TENANT_ID, PROPERTIES_CONFIG_CRED_USER, PROPERTIES_CONFIG_CRED_KEYSTONE_URL
import json
import sys


class FiwareTestCase(unittest.TestCase):

    # Spain region, by default
    region_name = 'Spain'

    # Temporal test data
    test_world = dict()

    @classmethod
    def __load_project_properties(cls):
        """
        Parse the JSON configuration file located in the settings folder and
        store the resulting dictionary in the config class variable.
        """

        print "Loading test properties"
        with open(PROPERTIES_FILE) as config_file:
            try:
                cls.conf = json.load(config_file)
            except Exception, e:
                print 'Error parsing config file: %s' % e
                sys.exit(1)

    @classmethod
    def init_world(cls):
        """
        Init the 'world' variable to store created data by Test Cases
        :return: None
        """
        cls.test_world.update({'servers': list(), 'sec_groups': list(), 'keypair_names': list(), 'networks': list(),
                               'routers': list(), 'allocated_ips': list()})

    @classmethod
    def setUpClass(cls):
        """
        SetUp all test cases. Init REST-Clients.
        Will be execute before ALL tests.
        :return: None
        """
        cls.__load_project_properties()

        print "SetUp Class - test case for '{region_name}' region".format(region_name=cls.region_name)
        cls.nova_operations = FiwareNovaOperations(
                                                cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_USER],
                                                cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_PASS],
                                                cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID],
                                                cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_KEYSTONE_URL],
                                                cls.region_name)
        cls.neutron_operations = FiwareNeutronOperations(
                                                cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_USER],
                                                cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_PASS],
                                                cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID],
                                                cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_KEYSTONE_URL],
                                                cls.region_name)

        # Init world variables
        cls.init_world()

    @classmethod
    def tearDownClass(cls):
        None
