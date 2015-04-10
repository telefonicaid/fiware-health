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


from tests import fiware_region_base_tests
from commons.constants import *
from novaclient.exceptions import Forbidden, OverLimit, ClientException as NovaClientException
from neutronclient.common.exceptions import NeutronClientException
from datetime import datetime


class FiwareRegionWithNetworkTest(fiware_region_base_tests.FiwareRegionsBaseTests):

    def __deploy_instance_helper__(self, instance_name, network_name=None, network_cidr=None, keypair_name=None,
                                   sec_group_name=None, metadata=None):
        """
        HELPER. Creates an instance with the given data. If param is None, that one will not passed to Nova.
            - Creates network if network_name is not None
            - Creates Keypair if keypair_name is not None
            - Creates Sec. Group if sec_group_name is not None
            - Adds metadata to server with teh given metadata dict.
        :param instance_name: Name of the new instance
        :param network_name: Name of the new network
        :param network_cidr: CIDR to be used by the subnet
        :param keypair_name: Name of the new keypair
        :param sec_group_name: Name of the new Sec. Group
        :param metadata: Python dict with metadata info {"key": "value"}
        :return: None
        """

        # skip if not all servers were deleted
        if self.test_world['servers']:
            self.skipTest("Not all the servers were deleted")

        flavor_id = self.nova_operations.get_any_flavor_id()
        self.assertIsNotNone(flavor_id, "Problems retrieving a flavor")

        image_id = self.nova_operations.find_image_id_by_name(image_name=BASE_IMAGE_NAME)
        self.assertIsNotNone(image_id, "Problems retrieving the image '{}'".format(BASE_IMAGE_NAME))

        # instance prerequisites
        try:
            network_id_list = None
            if network_name:
                cidr = network_cidr or TEST_DEFAULT_CIDR
                network = self.neutron_operations.create_network_and_subnet(network_name, cidr=cidr)
                self.test_world['networks'].append(network['id'])
                network_id_list = [{'net-id': network['id']}]

            if keypair_name:
                self.nova_operations.create_keypair(keypair_name)
                self.test_world['keypair_names'].append(keypair_name)

            security_group_name_list = None
            if sec_group_name:
                sec_group_id = self.nova_operations.create_security_group_and_rules(sec_group_name)
                self.test_world['sec_groups'].append(sec_group_id)
                security_group_name_list = [sec_group_name]
        except (NovaClientException, NeutronClientException) as e:
            self.logger.debug("Either required network or keypair or security group could not be created: %s", e)
            self.fail(e)

        # create new instance
        try:
            server_data = self.nova_operations.launch_instance(instance_name=instance_name,
                                                               flavor_id=flavor_id,
                                                               image_id=image_id,
                                                               metadata=metadata,
                                                               keypair_name=keypair_name,
                                                               security_group_name_list=security_group_name_list,
                                                               network_id_list=network_id_list)
        except Forbidden as e:
            self.logger.debug("Quota exceeded when launching a new instance")
            self.fail(e)
        except OverLimit as e:
            self.logger.debug("Not enough resources to launch new instance: %s", e)
            self.fail(e)
        else:
            self.test_world['servers'].append(server_data['id'])

        # Wait for status=ACTIVE
        status = self.nova_operations.wait_for_task_status(server_data['id'], 'ACTIVE')
        self.assertEqual(status, 'ACTIVE', "Server NOT ACTIVE after {seconds} seconds. Current status is {status}"
                         .format(seconds=MAX_WAIT_ITERATIONS*SLEEP_TIME, status=status))

    def test_create_network_and_subnet(self):
        """
        Test whether it is possible to create a new network with subnets
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_DEFAULT_CIDR
        network = self.neutron_operations.create_network_and_subnet(network_name, cidr=network_cidr)
        self.assertIsNotNone(network, "Problems creating network")
        self.assertEqual(network['status'], 'ACTIVE', "Network status is not ACTIVE")
        self.test_world['networks'].append(network['id'])
        self.logger.debug("%s", network)

    def test_external_networks(self):
        """
        Test whether there are external networks configured in the region
        """
        network_list = self.neutron_operations.find_networks(router_external=True)
        self.assertNotEqual(len(network_list), 0, "No external networks found")

    def test_create_router_no_external_network(self):
        """
        Test 10: Check if it is possible to create a new Router without setting the Gateway
        """
        router_name = "testing_router_01"
        router = self.neutron_operations.create_router(router_name)
        self.assertIsNotNone(router, "Problems creating router")
        self.assertEqual(router['status'], 'ACTIVE', "Router status is not ACTIVE")

        self.test_world['routers'].append(router['id'])

    def test_create_router_external_network(self):
        """
        Test 11: Check if it is possible to create a new Router, with a default Gateway
        """
        # Get the first external network id
        external_network_id = None
        external_network_list = self.neutron_operations.get_network_external_list()
        if len(external_network_list) != 0:
            external_net_region = self.conf[PROPERTIES_CONFIG_REGION][PROPERTIES_CONFIG_REGION_EXTERNAL_NET]
            if self.region_name in external_net_region:
                ext_net_config = external_net_region[self.region_name]
                for external_network in external_network_list:
                    if external_network['name'] == ext_net_config:
                        external_network_id = external_network['id']
            if external_network_id is None:
                external_network_id = external_network_list[0]['id']
        self.assertIsNotNone(external_network_id, "No external networks has been found")

        router_name = "testing_router_02"
        router = self.neutron_operations.create_router(router_name, external_network_id)
        self.assertIsNotNone(router, "Problems creating router")
        self.assertEqual(router['status'], 'ACTIVE', "Router status is not ACTIVE")

        self.test_world['routers'].append(router['id'])

    def test_deploy_instance_with_new_network(self):
        """
        Test whether it is possible to deploy an instance with a new network
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_network_" + suffix
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_DEFAULT_CIDR
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name,
                                        network_cidr=network_cidr)

    def test_deploy_instance_with_new_network_and_metadata(self):
        """
        Test whether it is possible to deploy an instance with a new network and custom metadata
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_network_metadata_" + suffix
        instance_meta = {"test_item": "test_value"}
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_DEFAULT_CIDR
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name,
                                        network_cidr=network_cidr,
                                        metadata=instance_meta)

    def test_deploy_instance_with_new_network_and_keypair(self):
        """
        Test whether it is possible to deploy an instance with a new network and new keypair
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_network_keypair_" + suffix
        keypair_name = TEST_KEYPAIR_PREFIX + "_" + suffix
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_DEFAULT_CIDR
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name,
                                        network_cidr=network_cidr,
                                        keypair_name=keypair_name)

    def test_deploy_instance_with_new_network_and_sec_group(self):
        """
        Test whether it is possible to deploy an instance with a new network and new security group
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_network_sec_group_" + suffix
        sec_group_name = TEST_SEC_GROUP_PREFIX + "_" + suffix
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_DEFAULT_CIDR
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name,
                                        network_cidr=network_cidr,
                                        sec_group_name=sec_group_name)

    def test_deploy_instance_with_new_network_and_all_params(self):
        """
        Test whether it is possible to deploy an instance with a new network and all params
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_network_all_params_" + suffix
        instance_meta = {"test_item": "test_value"}
        keypair_name = TEST_KEYPAIR_PREFIX + "_" + suffix
        sec_group_name = TEST_SEC_GROUP_PREFIX + "_" + suffix
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_DEFAULT_CIDR
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name,
                                        network_cidr=network_cidr,
                                        metadata=instance_meta,
                                        keypair_name=keypair_name,
                                        sec_group_name=sec_group_name)
