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
from novaclient.exceptions import Forbidden, OverLimit
from datetime import datetime
from commons.ssh_client import SSHClient, AuthenticationException
import socket


class FiwareRegionsBaseTests(FiwareTestCase):

    region_conf = None
    glance_conf = None

    @classmethod
    def setUpClass(cls):
        super(FiwareRegionsBaseTests, cls).setUpClass()
        cls.region_conf = cls.conf[PROPERTIES_CONFIG_REGION]
        cls.glance_conf = cls.conf[PROPERTIES_CONFIG_GLANCE]

    def setUp(self):
        super(FiwareRegionsBaseTests, self).setUp()
        self.test_world = {}
        self.init_world(self.test_world)

    def __create_keypair_test_helper__(self, keypair_name):
        """
        HELPER. Creates new Keypair
        :return: Private key value (String)
        """
        try:
            keypair_value = self.nova_operations.create_keypair(keypair_name)
            self.assertIsNotNone(keypair_value, "Problems creating keypair '%s" % keypair_name)
            self.test_world['keypair_names'].append(keypair_name)
        except Forbidden as e:
            self.logger.debug("Quota exceeded when creating a keypair")
            self.fail(e)

        return keypair_value

    def __allocate_ip_test_helper__(self):
        """
        HELPER. Allocates a IP from the Public Pool of the region
        :return IP address (String)
        """
        net = self.region_conf[PROPERTIES_CONFIG_REGION_EXTERNAL_NET][self.region_name]
        try:
            allocated_ip_data = self.nova_operations.allocate_ip(net)
            self.assertIsNotNone(allocated_ip_data, "Problems allocating IP from pool '%s'" % net)
            self.test_world['allocated_ips'].append(allocated_ip_data['id'])
        except OverLimit as e:
            self.logger.debug("Quota exceeded when allocating IP from pool '%s'", net)
            self.fail(e)

        return allocated_ip_data['ip']

    def __ssh_connection_test_helper__(self, host, private_key):
        """
        HELPER. Tries to connect (SSH) to the given host and retries if some failed (socket error)
        :param host: IP or Hostname (String)
        :param private_key: Private key value (String)
        :return:
        """
        ssh_client = SSHClient(self.logger, host=host, username='root', private_key=private_key)
        try:
            ssh_client.connect_and_retry()
        except AuthenticationException as e:
            self.logger.debug("Authentication failed when connecting (SSH) to VM %s, when trying to connect "
                              "for more than %d seconds", host, MAX_WAIT_SSH_CONNECT_ITERATIONS * SLEEP_TIME)
            self.fail(e)
        except socket.error as e:
            self.logger.debug("SSH connection error to VM %s, when trying to connect "
                              "for more than %d seconds", host, MAX_WAIT_SSH_CONNECT_ITERATIONS * SLEEP_TIME)
            self.fail(e)
        finally:
            ssh_client.close()

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

        # Filter out images with 'sdc_aware' metadata (named this way for historical reasons) attribute set to True
        image_list = [image for image in image_list if image.metadata.get('sdc_aware', "false").lower() == "true"]

        self.assertNotEqual(len(image_list), 0, "Cloud-init-aware image list is empty")
        self.logger.debug("Found %d images", len(image_list))

    def test_required_images(self):
        """
        Test whether region has all required base images (as specified in settings)
        """
        image_list = self.nova_operations.get_image_list()
        required_list = self.glance_conf.get(PROPERTIES_CONFIG_GLANCE_IMAGES, [])

        # Filter out required images not found in image list
        image_list = [image for image in required_list if not image in image_list]

        self.assertEqual(len(image_list), 0, "Required images %s not found" % image_list)
        self.logger.debug("Found required images %s", required_list)

    def test_base_image_for_testing_exists(self):
        """
        Test whether region has the image used for testing
        """
        base_image_name = self.nova_operations.test_image
        image_id = self.nova_operations.find_image_id_by_name(base_image_name)
        self.assertIsNotNone(image_id, "Problems retrieving image '%s'" % base_image_name)

    def test_create_security_group_and_rules(self):
        """
        Test creation of a new security group with rules
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        sec_group_name = TEST_SEC_GROUP_PREFIX + "_" + suffix
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
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        keypair_name = TEST_KEYPAIR_PREFIX + "_" + suffix
        self.__create_keypair_test_helper__(keypair_name)

    def test_allocate_ip(self):
        """
        Test allocation of a public IP
        """
        self.__allocate_ip_test_helper__()

    def tearDown(self):
        """
        Clean all test data from the environment after each test execution.
        """

        if self.test_world.get('servers'):
            self.logger.debug("Tearing down servers...")
            self.reset_world_servers(self.test_world)

        if self.test_world.get('sec_groups'):
            self.logger.debug("Tearing down security groups...")
            self.reset_world_sec_groups(self.test_world)

        if self.test_world.get('keypair_names'):
            self.logger.debug("Tearing down keypairs...")
            self.reset_world_keypair_names(self.test_world)

        if self.test_world.get('ports'):
            self.logger.debug("Tearing down ports...")
            self.reset_world_ports(self.test_world)

        if self.test_world.get('networks'):
            self.logger.debug("Tearing down networks...")
            self.reset_world_networks(self.test_world)

        if self.test_world.get('routers'):
            self.logger.debug("Tearing down routers...")
            self.reset_world_routers(self.test_world)

        if self.test_world.get('allocated_ips'):
            self.logger.debug("Tearing down allocated IPs...")
            self.reset_world_allocated_ips(self.test_world)

        if self.test_world.get('containers'):
            self.logger.debug("Tearing down containers...")
            self.reset_world_containers(self.test_world)

        if self.test_world.get('local_objects'):
            self.logger.debug("Tearing down local objects...")
            self.reset_world_local_objects(self.test_world)
