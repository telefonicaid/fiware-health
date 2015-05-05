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


from tests.fiware_region_base_tests import FiwareRegionsBaseTests
from commons.constants import *
from novaclient.exceptions import Forbidden, OverLimit, ClientException as NovaClientException
from neutronclient.common.exceptions import NeutronClientException, IpAddressGenerationFailureClient
from swiftclient.exceptions import ClientException as SwiftClientException
from datetime import datetime
from commons.http_phonehome_server import HttpPhoneHomeServer, get_phonehome_content, reset_phonehome_content
from commons.template_utils import replace_template_properties
import urlparse
import re


class FiwareRegionWithNetworkWithStorageTest(FiwareRegionsBaseTests):

    def __deploy_instance_helper__(self, instance_name,
                                   network_name=None, network_cidr=None, is_network_new=True,
                                   keypair_name=None, is_keypair_new=True,
                                   sec_group_name=None, metadata=None, userdata=None):
        """
        HELPER. Creates an instance with the given data. If param is None, that one will not passed to Nova.
            - Creates network if network_name is not None
            - Creates Keypair if keypair_name is not None
            - Creates Sec. Group if sec_group_name is not None
            - Adds metadata to server with teh given metadata dict.
        :param instance_name: Name of the new instance
        :param network_name: Name of the new network
        :param network_cidr: CIDR to be used by the subnet
        :param is_network_new: If True, a new network will be created; Else, test will suppose the network exists
                              (looking for it by network_name). In this case, the network will no be append to
                              Test World. If new_network is False, is_network_new will not be used.
        :param keypair_name: Name of the new keypair
        :param is_keypair_new: If True, a new keypair will be created to be used by Server; Else, test will suppose the
                                keypair already exists (looking for it by keypair_name). In this case, the keypair will
                                not be append to Test World.
        :param sec_group_name: Name of the new Sec. Group
        :param metadata: Python dict with metadata info {"key": "value"}
        :param userdata: userdata file content (String)
        :return: Server ID (String)
        """

        flavor_id = self.nova_operations.get_any_flavor_id()
        self.assertIsNotNone(flavor_id, "Problems retrieving a flavor")

        image_id = self.nova_operations.find_image_id_by_name(image_name=BASE_IMAGE_NAME)
        self.assertIsNotNone(image_id, "Problems retrieving the image '{}'".format(BASE_IMAGE_NAME))

        # instance prerequisites
        try:
            network_id_list = None
            if network_name:
                if is_network_new:
                    # Create the given network
                    cidr = network_cidr or TEST_CIDR_DEFAULT
                    network = self.neutron_operations.create_network_and_subnet(network_name, cidr=cidr)
                    self.test_world['networks'].append(network['id'])
                    network_id_list = [{'net-id': network['id']}]
                else:
                    # Look for the network id
                    net_list = self.neutron_operations.find_networks(name=network_name)
                    self.assertTrue(len(net_list) != 0, "Required network '%s' could not be found" % network_name)
                    network_id_list = [{'net-id': net_list[0]['id']}]

        except NeutronClientException as e:
            self.logger.debug("Required network could not be created: %s", e)
            self.fail(e)

        try:
            if keypair_name:
                if is_keypair_new:
                    self.nova_operations.create_keypair(keypair_name)
                    self.test_world['keypair_names'].append(keypair_name)
                else:
                    keypair_found = self.nova_operations.find_keypair(name=keypair_name)
                    self.assertIsNotNone(keypair_found, "Required Keypair '%s' could not be found" % keypair_name)
        except NovaClientException as e:
            self.logger.debug("Required keypair could not be created: %s", e)
            self.fail(e)

        try:
            security_group_name_list = None
            if sec_group_name:
                sec_group_id = self.nova_operations.create_security_group_and_rules(sec_group_name)
                self.test_world['sec_groups'].append(sec_group_id)
                security_group_name_list = [sec_group_name]
        except NovaClientException as e:
            self.logger.debug("Required security group could not be created: %s", e)
            self.fail(e)

        # create new instance
        try:
            server_data = self.nova_operations.launch_instance(instance_name=instance_name,
                                                               flavor_id=flavor_id,
                                                               image_id=image_id,
                                                               metadata=metadata,
                                                               keypair_name=keypair_name,
                                                               security_group_name_list=security_group_name_list,
                                                               network_id_list=network_id_list,
                                                               userdata=userdata)
        except Forbidden as e:
            self.logger.debug("Quota exceeded when launching a new instance")
            self.fail(e)
        except OverLimit as e:
            self.logger.debug("Not enough resources to launch new instance: %s", e)
            self.fail(e)
        else:
            self.test_world['servers'].append(server_data['id'])

        # Wait for status=ACTIVE
        status, detail = self.nova_operations.wait_for_task_status(server_data['id'], 'ACTIVE')
        self.assertEqual(status, 'ACTIVE', "{detail}. Current status is {status}".format(detail=detail, status=status))

        return server_data['id']

    def __get_external_network_test_helper__(self):
        """
        HELPER. Finds and returns the external network id
        :return: External network id
        """
        external_network_id = None
        external_network_list = self.neutron_operations.find_networks(router_external=True)
        if len(external_network_list) != 0:
            external_net_region = self.conf[PROPERTIES_CONFIG_REGION][PROPERTIES_CONFIG_REGION_EXTERNAL_NET]
            if self.region_name in external_net_region:
                ext_net_config = external_net_region[self.region_name]
                for external_network in external_network_list:
                    if external_network['name'] == ext_net_config:
                        external_network_id = external_network['id']
            if external_network_id is None:
                external_network_id = external_network_list[0]['id']
        self.assertIsNotNone(external_network_id, "No external networks found")

        return external_network_id

    def __create_router_test_helper__(self, router_name, external_network_id=None):
        """
        HELPER. Creates a router and links it to an external network (if not None)
        :param external_network_id: External network id
        :return: Router id (String)
        """

        try:
            router = self.neutron_operations.create_router(router_name, external_network_id)
        except IpAddressGenerationFailureClient as e:
            self.logger.debug("An error occurred creating router: %s", e)
            self.fail(e)
        self.assertIsNotNone(router, "Problems creating router")
        self.assertEqual(router['status'], 'ACTIVE', "Router status is NOT ACTIVE")
        self.test_world['routers'].append(router['id'])
        self.logger.debug("%s", router)

        return router['id']

    def __create_network_and_subnet_test_helper__(self, network_name, network_cidr):
        """
        HELPER. Creates network and subnet.
        :param network_name: Network name
        :param network_cidr: CIDR to use in the network
        :return: (NetworkId, SubnetworkId) (String, String)
        """
        network = self.neutron_operations.create_network_and_subnet(network_name, cidr=network_cidr)
        self.assertIsNotNone(network, "Problems creating network")
        self.assertEqual(network['status'], 'ACTIVE', "Network status is not ACTIVE")
        self.test_world['networks'].append(network['id'])
        self.logger.debug("%s", network)

        return network['id'], network['subnet']['id']

    def test_create_network_and_subnet(self):
        """
        Test whether it is possible to create a new network with subnets
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_CIDR_PATTERN % 254
        self.__create_network_and_subnet_test_helper__(network_name, network_cidr)

    def test_external_networks(self):
        """
        Test whether there are external networks configured in the region
        """
        network_list = self.neutron_operations.find_networks(router_external=True)
        self.assertNotEqual(len(network_list), 0, "No external networks found")

    def test_create_router_no_external_network(self):
        """
        Test whether it is possible to create a new router without setting the gateway
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        router_name = TEST_ROUTER_PREFIX + "_" + suffix
        self.__create_router_test_helper__(router_name)

    def test_create_router_no_external_network_and_add_network_port(self):
        """
        Test whether it is possible to create a new router without external gateway and link new network port
        """
        # Create Router
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        router_name = TEST_ROUTER_PREFIX + "_ports_" + suffix
        router_id = self.__create_router_test_helper__(router_name)

        # Create Network with only one subnet
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_CIDR_PATTERN % 253
        network_id, subnet_id = self.__create_network_and_subnet_test_helper__(network_name, network_cidr)

        port_id = self.neutron_operations.add_interface_router(router_id, subnet_id)
        self.test_world['ports'].append(port_id)

    def test_create_router_external_network(self):
        """
        Test whether it is possible to create a new router with a default gateway
        """

        # skip test if suite couldn't start from an empty, clean list of allocated IPs (to avoid cascading failures)
        if self.suite_world['allocated_ips']:
            self.skipTest("There were pre-existing, not deallocated IPs")

        # First, get external network id
        external_network_id = self.__get_external_network_test_helper__()

        # Then, create router
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        router_name = TEST_ROUTER_PREFIX + "_ext_" + suffix
        self.__create_router_test_helper__(router_name, external_network_id)

    def test_deploy_instance_with_new_network(self):
        """
        Test whether it is possible to deploy an instance with a new network
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_network_" + suffix
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_CIDR_PATTERN % 252
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
        network_cidr = TEST_CIDR_PATTERN % 251
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
        network_cidr = TEST_CIDR_PATTERN % 250
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
        network_cidr = TEST_CIDR_PATTERN % 249
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
        network_cidr = TEST_CIDR_PATTERN % 248
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name,
                                        network_cidr=network_cidr,
                                        metadata=instance_meta,
                                        keypair_name=keypair_name,
                                        sec_group_name=sec_group_name)

    def test_deploy_instance_with_network_and_associate_public_ip(self):
        """
        Test whether it is possible to deploy an instance with a new network and assign an allocated public IP
        """

        # skip test if suite couldn't start from an empty, clean list of allocated IPs (to avoid cascading failures)
        if self.suite_world['allocated_ips']:
            self.skipTest("There were pre-existing, not deallocated IPs")

        # Allocate IP
        allocated_ip = self.__allocate_ip_test_helper__()

        # Create Router with an external network gateway
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        router_name = TEST_ROUTER_PREFIX + "_public_ip_" + suffix
        external_network_id = self.__get_external_network_test_helper__()
        router_id = self.__create_router_test_helper__(router_name, external_network_id)

        # Create Network
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_CIDR_PATTERN % 247
        network_id, subnet_id = self.__create_network_and_subnet_test_helper__(network_name, network_cidr)

        # Add interface to router
        port_id = self.neutron_operations.add_interface_router(router_id, subnet_id)
        self.test_world['ports'].append(port_id)

        # Deploy VM (it will have only one IP from the Public Pool)
        instance_name = TEST_SERVER_PREFIX + "_public_ip_" + suffix
        server_id = self.__deploy_instance_helper__(instance_name=instance_name,
                                                    network_name=network_name, is_network_new=False)

        # Associate Public IP to Server
        self.nova_operations.add_floating_ip_to_instance(server_id=server_id, ip_address=allocated_ip)

    def test_deploy_instance_with_networks_and_e2e_connection_using_public_ip(self):
        """
        Test whether it is possible to deploy and instance, assign an allocated public IP and establish a SSH connection
        """

        # skip test if suite couldn't start from an empty, clean list of allocated IPs (to avoid cascading failures)
        if self.suite_world['allocated_ips']:
            self.skipTest("There were pre-existing, not deallocated IPs")

        # Allocate an IP
        allocated_ip = self.__allocate_ip_test_helper__()

        # Create Keypair
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        keypair_name = TEST_KEYPAIR_PREFIX + "_" + suffix
        private_keypair_value = self.__create_keypair_test_helper__(keypair_name)

        # Create Router with an external network gateway
        router_name = TEST_ROUTER_PREFIX + "_e2e_" + suffix
        external_network_id = self.__get_external_network_test_helper__()
        router_id = self.__create_router_test_helper__(router_name, external_network_id)

        # Create Network
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_CIDR_PATTERN % 246
        network_id, subnet_id = self.__create_network_and_subnet_test_helper__(network_name, network_cidr)

        # Add interface to router
        port_id = self.neutron_operations.add_interface_router(router_id, subnet_id)
        self.test_world['ports'].append(port_id)

        # Deploy VM (it will have only one IP from the Public Pool)
        instance_name = TEST_SERVER_PREFIX + "_e2e_" + suffix
        keypair_name = TEST_KEYPAIR_PREFIX + "_" + suffix
        sec_group_name = TEST_SEC_GROUP_PREFIX + "_" + suffix
        server_id = self.__deploy_instance_helper__(instance_name=instance_name,
                                                    network_name=network_name, is_network_new=False,
                                                    keypair_name=keypair_name, is_keypair_new=False,
                                                    sec_group_name=sec_group_name)

        # Associate the public IP to Server
        self.nova_operations.add_floating_ip_to_instance(server_id=server_id, ip_address=allocated_ip)

        # SSH Connection
        self.__ssh_connection_test_helper__(host=allocated_ip, private_key=private_keypair_value)

    def test_deploy_instance_with_networks_and_e2e_snat_connection(self):
        """
        Test whether it is possible to deploy an instance with new network and connect to INTERNET (PhoneHome service)
        """

        # skip test if suite couldn't start from an empty, clean list of allocated IPs (to avoid cascading failures)
        if self.suite_world['allocated_ips']:
            self.skipTest("There were pre-existing, not deallocated IPs")

        # skip test if no PhoneHome service endpoint was given by configuration (either in settings or by environment)
        phonehome_endpoint = self.conf[PROPERTIES_CONFIG_TEST][PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT]
        if not phonehome_endpoint:
            self.skipTest("No value found for '{}.{}' setting".format(
                PROPERTIES_CONFIG_TEST, PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT))

        # Load userdata from file and compile the template (replacing {{phonehome_endpoint}} value)
        self.logger.debug("Loading userdata from file '%s'", PHONEHOME_USERDATA_PATH)
        with open(PHONEHOME_USERDATA_PATH, "r") as userdata_file:
            userdata_content = userdata_file.read()
            userdata_content = replace_template_properties(userdata_content, phonehome_endpoint=phonehome_endpoint)
            self.logger.debug("Userdata content: %s", userdata_content)
            phonehome_port = urlparse.urlsplit(phonehome_endpoint).port
            self.logger.debug("PhoneHome port to be used by server: %d", phonehome_port)

        # Create Router with an external network gateway
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        router_name = TEST_ROUTER_PREFIX + "_snat_" + suffix
        external_network_id = self.__get_external_network_test_helper__()
        router_id = self.__create_router_test_helper__(router_name, external_network_id)

        # Create Network
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_cidr = TEST_CIDR_PATTERN % 245
        network_id, subnet_id = self.__create_network_and_subnet_test_helper__(network_name, network_cidr)

        # Add interface to router
        port_id = self.neutron_operations.add_interface_router(router_id, subnet_id)
        self.test_world['ports'].append(port_id)

        # Deploy VM
        instance_name = TEST_SERVER_PREFIX + "_snat_" + suffix
        server_id = self.__deploy_instance_helper__(instance_name=instance_name,
                                                    network_name=network_name, is_network_new=False,
                                                    userdata=userdata_content)

        # Create and launch a PhoneHome service listening at <localhost:phonehome_port>. Wait for request from VM
        http_phonehome_server = HttpPhoneHomeServer(logger=self.logger, port=phonehome_port, timeout=PHONEHOME_TIMEOUT)
        http_phonehome_server.start()
        self.assertIsNotNone(get_phonehome_content(), "Phone-Home request not received from VM '%s'" % server_id)
        call_content = get_phonehome_content()
        self.logger.debug("Request received from VM when 'calling home': %s", call_content)

        # Get hostname from data received
        self.assertIn("hostname", call_content, "Phone-Home request has been received but 'hostname' param is not in")
        hostname_received = re.match(".*hostname=([\w-]*)", call_content).group(1)

        # Check hostname (VM will have as hostname, the instance_name with "-" instead of "_")
        self.assertEqual(instance_name.replace("_", "-"), hostname_received,
                         "Received hostname '%s' in PhoneHome request does not match with the expected instance name" %
                         hostname_received)

        reset_phonehome_content()

    def test_create_get_and_delete_container(self):
        """
        Test if it can be possible create a new container into the object storage, list it and delete the container.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        containerName = TEST_CONTAINER_PREFIX + suffix

        response = self.swift_operations.create_container(containerName)
        self.assertIsNone(response)
        self.test_world['containers'].append(containerName)
        self.logger.debug("Created %s container was created" % containerName)

        response = self.swift_operations.get_container(containerName)
        self.assertEquals('x-container-object-count' in response[0], True)
        self.assertEquals(len(response[-1]), 0)  # The list of items should be 0.
        self.logger.debug("Getting %s container details from the object storage" % containerName)

        response = self.swift_operations.delete_container(containerName)
        self.assertIsNone(response)
        self.test_world['containers'].remove(containerName)

        try:
            response = self.swift_operations.get_container(containerName)
        except SwiftClientException as e:
            self.assertRaises(e)
            self.logger.debug("%s container was successfully removed from the object storage" % containerName)

    def test_create_container(self):
        """
        Test if it can be possible create a new container into the object storage.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S%m')
        containerName = TEST_CONTAINER_PREFIX + suffix

        response = self.swift_operations.create_container(containerName)
        self.assertIsNone(response)
        self.test_world['containers'].append(containerName)
        self.logger.debug("Created %s container was created" % containerName)

