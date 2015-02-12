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


from tests import fiware_region_base_tests
from commons.constants import WAIT_FOR_INSTANCE_ACTIVE, SLEEP_TIME, BASE_IMAGE_NAME


class FiwareRegionWithNetkorkTest(fiware_region_base_tests.FiwareRegionsBaseTests):

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

        flavor_id = self.nova_operations.get_any_flavor_id()
        self.assertIsNotNone(flavor_id, "Problems retrieving a flavor")

        image_id = self.nova_operations.find_image_id_by_name(image_name=BASE_IMAGE_NAME)
        self.assertIsNotNone(image_id, "Problems retrieving the image '{}'".format(BASE_IMAGE_NAME))

        network_id_list = None
        if network_name is not None:
            cidr = network_cidr if network_cidr is not None else "10.250.254.0/24"
            network = self.neutron_operations.create_network_and_subnet(network_name, cidr=cidr)
            self.test_world['networks'].append(network['id'])
            network_id_list = [{'net-id': network['id']}]

        if keypair_name is not None:
            keypair_value = self.nova_operations.create_keypair(keypair_name)
            self.test_world['keypair_names'].append(keypair_name)

        security_group_name_list = None
        if sec_group_name is not None:
            sec_group_id = self.nova_operations.create_security_group_and_rules(sec_group_name)
            self.test_world['sec_groups'].append(sec_group_id)
            security_group_name_list = [sec_group_name]

        server_data = self.nova_operations.launch_instance(instance_name=instance_name, flavor_id=flavor_id,
                                                           image_id=image_id,
                                                           network_id_list=network_id_list,
                                                           metadata=metadata,
                                                           keypair_name=keypair_name,
                                                           security_group_name_list=security_group_name_list)
        self.test_world['servers'].append(server_data['id'])

        # Wait for status=ACTIVE
        status = self.nova_operations.wait_for_task_status(server_data['id'], 'ACTIVE')
        self.assertEqual(status, 'ACTIVE',
                         "Server launched is not ACTIVE after {seconds} seconds. Current Server status: {status}"
                         .format(seconds=WAIT_FOR_INSTANCE_ACTIVE*SLEEP_TIME, status=status))


    def test_create_network_and_subnet(self):
        """
        Test 08: Check if it is possible to create a new Network with subnets
        """
        network_name = "testingnetwork01"
        network = self.neutron_operations.create_network_and_subnet(network_name, cidr="10.250.250.0/24")
        self.assertIsNotNone(network, "Problems creating network")
        self.assertEqual(network['status'], 'ACTIVE', "Network status is not ACTIVE")

        self.test_world['networks'].append(network['id'])

    def test_there_are_external_networks(self):
        """
        Test 09: Check if there are external networks configured in the Region
        """
        network_list = self.neutron_operations.get_network_external_list()
        self.assertIsNotNone(network_list, "No external networks has been found")
        self.assertNotEqual(len(network_list), 0, "No external networks has been found")

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
            external_network_id = external_network_list[0]['id']
        self.assertIsNotNone(external_network_id, "No external networks has been found")

        router_name = "testing_router_02"
        router = self.neutron_operations.create_router(router_name, external_network_id)
        self.assertIsNotNone(router, "Problems creating router")
        self.assertEqual(router['status'], 'ACTIVE', "Router status is not ACTIVE")

        self.test_world['routers'].append(router['id'])

    def test_deploy_instance_with_new_network(self):
        """
        Test 12: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new NetworkID
        """
        self.__deploy_instance_helper__("testing_instance_02",
                                        network_name="testingnetwork02",
                                        network_cidr="10.250.251.0/24")

    def test_deploy_instance_with_new_network_and_metadatas(self):
        """
        Test 13: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new NetworkID, Metadatas
        """
        self.__deploy_instance_helper__("testing_instance_03",
                                        network_name="testingnetwork03",
                                        network_cidr="10.250.252.0/24",
                                        metadata={"metadatatest01": "qatesting01"})

    def test_deploy_instance_with_new_network_and_keypair(self):
        """
        Test 14: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new NetworkID, new Keypair
        """
        self.__deploy_instance_helper__("testing_instance_04",
                                        network_name="testingnetwork04",
                                        network_cidr="10.250.253.0/24",
                                        keypair_name="testing_keypair04")

    def test_deploy_instance_with_new_network_and_sec_group(self):
        """
        Test 15: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new NetworkID, new Sec. Group
        """
        self.__deploy_instance_helper__("testing_instance_05",
                                        network_name="testingnetwork05",
                                        network_cidr="10.250.254.0/24",
                                        sec_group_name="testing_sec_group_05")

    def test_deploy_instance_with_all_params(self):
        """
        Test 16: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, NetworkID, Sec. Group, keypair, metadata
        """
        self.__deploy_instance_helper__("testing_instance_06",
                                        network_name="testingnetwork06",
                                        network_cidr="10.250.254.0/24",
                                        keypair_name="testing_keypair06",
                                        sec_group_name="testing_sec_group_06",
                                        metadata={"metadatatest01": "qatesting01"})
