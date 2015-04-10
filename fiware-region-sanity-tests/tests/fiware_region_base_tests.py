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
        cls.region_conf = cls.conf[PROPERTIES_CONFIG_REGION]

    def test_flavors_not_empty(self):
        """
        Test whether region has flavors
        """
        flavor_list = self.nova_operations.get_flavor_list()
        self.assertNotEqual(len(flavor_list), 0, "Flavor list is empty")
        self.logger.debug("Available flavors: %s", [str(flavor.name) for flavor in flavor_list])

    def test_images_not_empty(self):
        """
        Test whether region has images
        """
        image_list = self.nova_operations.get_image_list()
        self.assertNotEqual(len(image_list), 0, "Image list is empty")
        self.logger.debug("Found %d available images", len(image_list))

    def test_cloud_init_aware_images(self):
        """
        Test whether region has 'cloud-init-aware' images (suitable for blueprints)
        """
        image_list = self.nova_operations.get_image_list()

        # Filter out images with 'init' in its name
        image_list = [image for image in image_list if 'init' in image.name]

        # Filter out images with 'sdc_aware' metadata attribute set to True
        image_list = [image for image in image_list if image.metadata.get('sdc_aware', "false").lower() == "true"]

        self.assertNotEqual(len(image_list), 0, "Cloud-init-aware image list is empty")
        self.logger.debug("Found %d images", len(image_list))

    def test_base_image_for_testing_exists(self):
        """
        Test whether region has the image used for testing
        """
        image_id = self.nova_operations.find_image_id_by_name(BASE_IMAGE_NAME)
        self.assertIsNotNone(image_id, "Problems retrieving image '%s'" % BASE_IMAGE_NAME)

    def test_create_security_group_and_rules(self):
        """
        Test creation of a new security group with rules
        """

        # skip if not all security groups were deleted
        if self.test_world['sec_groups']:
            self.skipTest("Not all the security groups were deleted")

        sec_group_name = TEST_SEC_GROUP_PREFIX
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

        keypair_name = TEST_KEYPAIR_PREFIX
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

        net = self.region_conf[PROPERTIES_CONFIG_REGION_EXTERNAL_NET][self.region_name]
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

        if self.test_world.get('servers'):
            self.logger.debug("Tearing down servers...")
            self.reset_world_servers()

        if self.test_world.get('sec_groups'):
            self.logger.debug("Tearing down security groups...")
            self.reset_world_sec_groups()

        if self.test_world.get('keypair_names'):
            self.logger.debug("Tearing down keypairs...")
            self.reset_world_keypair_names()

        if self.test_world.get('networks'):
            self.logger.debug("Tearing down networks...")
            self.reset_world_networks()

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
