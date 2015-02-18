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


from commons.fiware_cloud_test_case import FiwareTestCase
from commons.constants import BASE_IMAGE_NAME, PROPERTIES_CONFIG_REGION_CONFIG, \
    PROPERTIES_CONFIG_REGION_CONFIG_EXTERNAL_NET
from novaclient.exceptions import NotFound
import time


class FiwareRegionsBaseTests (FiwareTestCase):

    def setUp(self):
        print "Setting up Test Cases - ", self.region_name

    def test_flavors_not_empty(self):
        """
        Test 01: Check if the Region has flavors.
        """
        flavor_list = self.nova_operations.get_flavor_list()
        self.assertIsNotNone(flavor_list, "Flavor list is empty")
        self.assertNotEqual(len(flavor_list), 0, "Flavor list is empty")

    def test_images_not_empty(self):
        """
        Test 02: Check if the Region has images.
        """
        image_list = self.nova_operations.get_image_list()
        self.assertIsNotNone(image_list, "Image list is empty")
        self.assertNotEqual(len(image_list), 0, "Image list is empty")

    def test_there_are_init_images(self):
        """
        Test 03: Check if the Region has images with 'init' in the name.
        """
        image_list = self.nova_operations.get_image_list()
        self.assertIsNotNone(image_list, "Image list is empty")
        self.assertNotEqual(len(image_list), 0, "Image list is empty")

        found = False
        for image in image_list:
            if 'init' in image['name']:
                found = True
                break
        self.assertTrue(found, "No 'init' images has been found")

    def test_base_image_for_testing_exists(self):
        """
        Test 04: Check if the Region has the BASE_IMAGE_NAME used for testing
        """
        image_id = self.nova_operations.find_image_id_by_name(image_name=BASE_IMAGE_NAME)
        self.assertIsNotNone(image_id, "Problems retrieving the image '{}'".format(BASE_IMAGE_NAME))

    def test_create_security_group_and_rules(self):
        """
        Test 05: Check if it is possible to create a new Security Group with rules.
        """
        sec_group_name = "testing_sec_group"
        sec_group_id = self.nova_operations.create_security_group_and_rules(sec_group_name)
        self.assertIsNotNone(sec_group_id, "Problems creating Security Group")

        self.test_world['sec_groups'].append(sec_group_id)

    def test_create_keypair(self):
        """
        Test 06: Check if it is possible to create a new Keypair.
        """
        keypair_name = "testing_keypair"
        keypair_value = self.nova_operations.create_keypair(keypair_name)
        self.assertIsNotNone(keypair_value, "Problems creating Keypair")

        self.test_world['keypair_names'].append(keypair_name)

    def test_allocate_ip(self):
        """
        Test 07: Allocate a public IP
        :return:
        """
        net = self.conf[PROPERTIES_CONFIG_REGION_CONFIG][PROPERTIES_CONFIG_REGION_CONFIG_EXTERNAL_NET][self.region_name]
        allocated_ip_data = self.nova_operations.allocate_ip(net)
        self.assertIsNotNone(allocated_ip_data, "Problems allocating IP from pool: " + net)

        self.test_world['allocated_ips'].append(allocated_ip_data['id'])

    def tearDown(self):
        """
        TearDown. Clean all test data from the environment after each test execution.
        :return: None
        """

        print "TearDown - Removing generated test data"
        print str(self.test_world)

        error_message = ""
        if 'servers' in self.test_world:
            for server_id in self.test_world['servers']:
                try:
                    self.nova_operations.delete_instance(server_id)
                    self.nova_operations.wait_for_task_status(server_id, 'DELETED')
                except NotFound:
                    print "Server '{}' deleted".format(server_id)
                except Exception as detail:
                    error_message = error_message + "ERROR deleting instances. " + str(detail) + "\n"

            # Wait 5 seconds after Server deletion process
            time.sleep(5)

        if 'sec_groups' in self.test_world:
            for sec_group in self.test_world['sec_groups']:
                try:
                    self.nova_operations.delete_security_group(sec_group)
                except Exception as detail:
                    error_message = error_message + "ERROR deleting security groups. " + str(detail) + "\n"

        if 'keypair_names' in self.test_world:
            for keypair_name in self.test_world['keypair_names']:
                try:
                    self.nova_operations.delete_keypair(keypair_name)
                except Exception as detail:
                    error_message = error_message + "ERROR deleting keypairs. " + str(detail) + "\n"

        if 'networks' in self.test_world:
            for network_id in self.test_world['networks']:
                try:
                    self.neutron_operations.delete_network(network_id)
                except Exception as detail:
                    error_message = error_message + "ERROR deleting networks. " + str(detail) + "\n"

        if 'routers' in self.test_world:
            for router_id in self.test_world['routers']:
                try:
                    self.neutron_operations.delete_router(router_id)
                except Exception as detail:
                    error_message = error_message + "ERROR deleting routers. " + str(detail) + "\n"

        if 'allocated_ips' in self.test_world:
            for ip_id in self.test_world['allocated_ips']:
                try:
                    self.nova_operations.deallocate_ip(ip_id)
                except Exception as detail:
                    error_message = error_message + "ERROR deallocating IP. " + str(detail) + "\n"

        #Init world after cleaning
        self.init_world()

        if error_message != "":
            raise Exception(error_message)
