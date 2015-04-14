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


from commons.paas_manager_test_case import PaaSManagerTestCase


class PaaSManagerSmokeTestSuite(PaaSManagerTestCase):

    def setUp(self):
        """
        Setup TestCase.
            -> Init TestWorld
        :return: none
        """
        self.init_test_world()

    def test_create_environment(self):
        """
        Test 01: Create new environment (Tenant environment)
        """
        env_name = "QAEnv"
        response = self.paasmanager_client.getEnvironmentResourceClient().create_environment(env_name,
                                                                                             "For testing purposes")
        self.assertTrue(response.ok, "ERROR creating environment {}. Response: {}".format(env_name, str(response.content)))
        self.test_world['environment'].append(env_name)

    def tearDown(self):
        """
        Teardown.
            -> Clean all created environments.
        :return:
        """
        self.clean_environments()
