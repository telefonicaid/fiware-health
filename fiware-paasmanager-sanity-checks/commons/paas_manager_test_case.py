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

from paasmanager_client.client import PaaSManagerClient
from commons.constants import *
import unittest
import json
import os


class PaaSManagerTestCase(unittest.TestCase):

    conf = None
    paasmanager_client = None
    test_world = dict()

    @classmethod
    def __load_project_properties__(cls):
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

    @classmethod
    def init_test_world(cls):
        """
        Init test world. Test data will be stored in this var to be cleaned up in teardown process
        :return: None
        """
        cls.test_world.update({'environment': list()})

    @classmethod
    def clean_environments(cls):
        """
        Clean all environemnts stored in TestWorld.
            -> Remove environemnt from PaaSManager
        :return: None
        """
        failed = False
        for environemnt in cls.test_world['environment']:
            response = cls.paasmanager_client.getEnvironmentResourceClient().delete_environment(environemnt)
            if not response.ok:
                print "ERROR deleting environment {}. Message: {}".format(environemnt, str(response.content)),
                failed = True

        assert failed is False, "ERROR(s) deleting environments"

    @classmethod
    def setUpClass(cls):
        """
        Setup Suite.
            -> Load properties from file
            -> Init PaaSManagerClient
        :return: None
        """
        cls.__load_project_properties__()

        tenant_id = os.getenv('OS_TENANT_ID', cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID])
        username = os.getenv('OS_USERNAME', cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_USER])
        password = os.getenv('OS_PASSWORD', cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_PASS])
        region_name = os.getenv('OS_REGION_NAME', cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_REGION_NAME])
        auth_url = os.getenv('OS_AUTH_URL', cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_AUTH_URL])

        cls.paasmanager_client = PaaSManagerClient(tenant_id=tenant_id, username=username, password=password,
                                                   region_name=region_name, auth_url=auth_url)

    @classmethod
    def tearDownClass(cls):
        None
