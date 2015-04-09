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


from commons.fiware_cloud_test_case import FiwareTestCase
from commons.constants import *
from novaclient.exceptions import NotFound, Forbidden
import time


class FiwareRegionsBaseTests(FiwareTestCase):

    region_conf = None

    @classmethod
    def setUpClass(cls):
        super(FiwareRegionsBaseTests, cls).setUpClass()
        cls.region_conf = cls.conf[PROPERTIES_CONFIG_REGION_CONFIG]

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
        Test creation of a new security group with rules
        """

        # skip if not all security groups were deleted
        if self.test_world['sec_groups']:
            self.skipTest("Not all the security groups were deleted")

        sec_group_name = TEST_SEC_GROUP
        try:
            sec_group_id = self.nova_operations.create_security_group_and_rules(sec_group_name)
            self.assertIsNotNone(sec_group_id, "Problems creating security group '%s'" % sec_group_name)
            self.test_world['sec_groups'].append(sec_group_id)
        except Forbidden as e:
            self.logger.debug("Quota exceeded when creating a security group")
            self.fail(e)

    def test_create_keypair(self):
        """
        Test creation of a new keypair
        """

        # skip if not all keypairs were deleted
        if self.test_world['keypair_names']:
            self.skipTest("Not all the keypairs were deleted")

        keypair_name = TEST_KEYPAIR
        try:
            keypair_value = self.nova_operations.create_keypair(keypair_name)
            self.assertIsNotNone(keypair_value, "Problems creating keypair '%s" % keypair_name)
            self.test_world['keypair_names'].append(keypair_name)
        except Forbidden as e:
            self.logger.debug("Quota exceeded when creating a keypair")
            self.fail(e)

    def test_allocate_ip(self):
        """
        Test allocation of a public IP
        """

        # skip if not all IPs were deallocated
        if self.test_world['allocated_ips']:
            self.skipTest("Not all the IPs were deallocated")

        net = self.region_conf[PROPERTIES_CONFIG_REGION_CONFIG_EXTERNAL_NET][self.region_name]
        try:
            allocated_ip_data = self.nova_operations.allocate_ip(net)
            self.assertIsNotNone(allocated_ip_data, "Problems allocating IP from pool '%s'" % net)
            self.test_world['allocated_ips'].append(allocated_ip_data['id'])
        except Forbidden as e:
            self.logger.debug("Quota exceeded when allocating IP from pool '%s'", net)
            self.fail(e)

    def tearDown(self):
        """
        Clean all test data from the environment after each test execution.
        """

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

        if self.test_world.get('sec_groups'):
            self.logger.debug("Tearing down security groups...")
            self.reset_world_sec_groups()

        if self.test_world.get('keypair_names'):
            self.logger.debug("Tearing down keypairs...")
            self.reset_world_keypair_names()

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

        if self.test_world.get('allocated_ips'):
            self.logger.debug("Tearing down allocated IPs...")
            self.reset_world_allocated_ips()

        if error_message != "":
            raise Exception(error_message)
