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


from tests.fiware_region_base_tests import FiwareRegionsBaseTests
from commons.constants import *
from novaclient.exceptions import Forbidden, OverLimit, ClientException as NovaClientException
from neutronclient.common.exceptions import NeutronClientException, IpAddressGenerationFailureClient
from datetime import datetime
from commons.dbus_phonehome_service import DbusPhoneHomeClient
from commons.template_utils import replace_template_properties
from commons.constants import PHONEHOME_TX_ID_HEADER
import re
import json
import uuid


def _build_path_resource(path_resource):
    """Build url path with a transactionId param"""
    return '{0}?{1}={2}'.format(path_resource, PHONEHOME_TX_ID_HEADER, str(uuid.uuid1()))


class FiwareRegionWithNetworkTest(FiwareRegionsBaseTests):

    with_networks = True

    def __deploy_instance_helper__(self, instance_name,
                                   network_name=None, is_network_new=True, cidr=None,
                                   keypair_name=None, is_keypair_new=True,
                                   sec_group_name=None, metadata=None, userdata=None):
        """
        HELPER. Creates a new instance according to the given parameters:
        - If a network name is given, a new network (`is_network_new==True`) or an existing one is associated.
        - If a keypair name is given, a new keypair (`is_keypair_new==True`) or an existing one is associated.
        - If a security group name is given, a new sec_group is created and associated to the instance.
        - Optional metadata and userdata may also be associated.

        :param instance_name: Name of the new instance
        :param network_name: Name of the network to use (either existing or a new one)
        :param is_network_new: If True, a new network should be created and appended to the `TestWorld`
        :param cidr: Optional CIDR to use in the network's subnet (otherwise, one is chosen from default range)
        :param keypair_name: Name of the keypair to use (either existing or a new one)
        :param is_keypair_new: If True, a new keypair should be created and appended to the `TestWorld`
        :param sec_group_name: Name of the new security group that will be created
        :param metadata: Python dict with metadata info {"key": "value"}
        :param userdata: userdata file content (String)
        :return: Server ID (String)
        """

        flavor_id = self.nova_operations.get_any_flavor_id()
        self.assertIsNotNone(flavor_id, "Problems retrieving a flavor")

        base_image_name = self.nova_operations.test_image
        image_id = self.nova_operations.find_image_id_by_name(image_name=base_image_name)
        self.assertIsNotNone(image_id, "Problems retrieving the image '{}'".format(base_image_name))

        # instance prerequisites
        try:
            network_id_list = None
            if network_name:
                if is_network_new:
                    # Create the given network
                    network = self.neutron_operations.create_network(network_name)
                    self.test_world['networks'].append(network['id'])
                    network_id_list = [{'net-id': network['id']}]
                    # Create a subnet
                    self.neutron_operations.create_subnet(network, cidr)
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
        HELPER. Finds and returns the external network id of current region
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

    def __get_shared_network_test_helper__(self):
        """
        HELPER. Finds and returns the shared network name of current region
        :return: Shared network name
        """
        # get from settings the name of the shared network to lookup
        lookup_network_name = TEST_SHARED_NET_DEFAULT
        shared_network_conf = self.conf[PROPERTIES_CONFIG_REGION].get(PROPERTIES_CONFIG_REGION_SHARED_NET)
        if shared_network_conf:
            lookup_network_name = shared_network_conf.get(self.region_name, TEST_SHARED_NET_DEFAULT)

        # find the network in the list of existing shared networks
        lookup_network_list = self.neutron_operations.find_networks(name=lookup_network_name,
                                                                    shared=True,
                                                                    router_external=False)
        shared_network_name = lookup_network_list[0]['name'] if lookup_network_list else None
        self.assertIsNotNone(shared_network_name, "No shared network %s found" % lookup_network_name)

        return shared_network_name

    def __e2e_connection_using_public_ip_test_helper__(self, use_shared_network=True):
        """
        HELPER. Test whether it is possible to deploy an instance, assign an allocated public IP and establish
        a SSH connection

        :param use_shared_network: If True, use the existing shared network associated to the new instance
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

        # Network
        if use_shared_network:
            network_name = self.__get_shared_network_test_helper__()
        else:
            # Create Router with an external network gateway
            router_name = TEST_ROUTER_PREFIX + "_e2e_" + suffix
            external_network_id = self.__get_external_network_test_helper__()
            router_id = self.__create_router_test_helper__(router_name, external_network_id)

            # Create Network
            network_name = TEST_NETWORK_PREFIX + "_" + suffix
            network_id, subnet_id = self.__create_network_and_subnet_test_helper__(network_name)

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

    def __e2e_snat_connection_test_helper__(self, use_shared_network=True):
        """
        HELPER. Test whether it is possible to deploy an instance and connect to the internet (PhoneHome service)

        :param use_shared_network: If True, use the existing shared network associated to the new instance
        """

        # skip test if suite couldn't start from an empty, clean list of allocated IPs (to avoid cascading failures)
        if self.suite_world['allocated_ips']:
            self.skipTest("There were pre-existing, not deallocated IPs")

        # skip test if no PhoneHome service endpoint was given by configuration (either in settings or by environment)
        phonehome_endpoint = self.conf[PROPERTIES_CONFIG_TEST][PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT]
        if not phonehome_endpoint:
            self.skipTest("No value found for '{}.{}' setting".format(
                PROPERTIES_CONFIG_TEST, PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT))

        path_resource = PHONEHOME_DBUS_OBJECT_PATH

        # Load userdata from file and compile the template (replacing variable values)
        self.logger.debug("Loading userdata from file '%s'", PHONEHOME_USERDATA_PATH)
        with open(PHONEHOME_USERDATA_PATH, "r") as userdata_file:
            userdata_content = userdata_file.read()
            userdata_content = replace_template_properties(userdata_content, phonehome_endpoint=phonehome_endpoint,
                                                           path_resource=_build_path_resource(path_resource))
            self.logger.debug("Userdata content: %s", userdata_content)

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')

        # Network
        if use_shared_network:
            network_name = self.__get_shared_network_test_helper__()
        else:
            # Create Router with an external network gateway
            router_name = TEST_ROUTER_PREFIX + "_snat_" + suffix
            external_network_id = self.__get_external_network_test_helper__()
            router_id = self.__create_router_test_helper__(router_name, external_network_id)

            # Create Network
            network_name = TEST_NETWORK_PREFIX + "_" + suffix
            network_id, subnet_id = self.__create_network_and_subnet_test_helper__(network_name)

            # Add interface to router
            port_id = self.neutron_operations.add_interface_router(router_id, subnet_id)
            self.test_world['ports'].append(port_id)

        # Deploy VM
        instance_name = self.region_name.lower() + "_" + TEST_SERVER_PREFIX + "_snat_" + suffix
        server_id = self.__deploy_instance_helper__(instance_name=instance_name,
                                                    network_name=network_name, is_network_new=False,
                                                    userdata=userdata_content)

        # VM will have as hostname, the instance_name with "-" instead of "_"
        expected_instance_name = instance_name.replace("_", "-")

        # Create new new DBus connection and wait for emitted signal from HTTP PhoneHome service
        client = DbusPhoneHomeClient(self.logger)
        result = client.connect_and_wait_for_phonehome_signal(PHONEHOME_DBUS_NAME, PHONEHOME_DBUS_OBJECT_PATH,
                                                              PHONEHOME_SIGNAL, expected_instance_name)
        self.assertIsNotNone(result, "PhoneHome request not received from VM '%s'" % server_id)
        self.logger.debug("Request received from VM when 'calling home': %s", result)

        # Get hostname from data received
        self.assertIn("hostname", result, "PhoneHome request has been received but 'hostname' param is not in")
        received_hostname = re.match(".*hostname=([\w-]*)", result).group(1)

        # Check hostname
        self.assertEqual(expected_instance_name, received_hostname,
                         "Received hostname '%s' in PhoneHome request does not match with the expected instance name" %
                         received_hostname)

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

    def __create_network_and_subnet_test_helper__(self, network_name, cidr=None):
        """
        HELPER. Creates network and subnet.
        :param network_name: Network name
        :param cidr: Optional CIDR to use in the subnet (otherwise, one is chosen from default range)
        :return: (NetworkId, SubnetworkId) (String, String)
        """
        network = self.neutron_operations.create_network(network_name)
        self.assertIsNotNone(network, "Problems creating network")
        self.assertEqual(network['status'], 'ACTIVE', "Network status is not ACTIVE")
        self.test_world['networks'].append(network['id'])
        network = self.neutron_operations.create_subnet(network, cidr)
        self.assertIsNotNone(network['subnet']['id'], "Problems creating subnet")
        self.logger.debug("%s", network)
        return network['id'], network['subnet']['id']

    def test_create_network_and_subnet(self):
        """
        Test whether it is possible to create a new network with subnets
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        self.__create_network_and_subnet_test_helper__(network_name)

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
        network_id, subnet_id = self.__create_network_and_subnet_test_helper__(network_name)

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
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name)

    def test_deploy_instance_with_new_network_and_metadata(self):
        """
        Test whether it is possible to deploy an instance with a new network and custom metadata
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_network_metadata_" + suffix
        instance_meta = {"test_item": "test_value"}
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name,
                                        metadata=instance_meta)

    def test_deploy_instance_with_new_network_and_keypair(self):
        """
        Test whether it is possible to deploy an instance with a new network and new keypair
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_network_keypair_" + suffix
        keypair_name = TEST_KEYPAIR_PREFIX + "_" + suffix
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name,
                                        keypair_name=keypair_name)

    def test_deploy_instance_with_new_network_and_sec_group(self):
        """
        Test whether it is possible to deploy an instance with a new network and new security group
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_network_sec_group_" + suffix
        sec_group_name = TEST_SEC_GROUP_PREFIX + "_" + suffix
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name,
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
        self.__deploy_instance_helper__(instance_name=instance_name,
                                        network_name=network_name,
                                        metadata=instance_meta,
                                        keypair_name=keypair_name,
                                        sec_group_name=sec_group_name)

    def test_deploy_instance_with_new_network_and_associate_public_ip(self):
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
        network_id, subnet_id = self.__create_network_and_subnet_test_helper__(network_name)

        # Add interface to router
        port_id = self.neutron_operations.add_interface_router(router_id, subnet_id)
        self.test_world['ports'].append(port_id)

        # Deploy VM (it will have only one IP from the Public Pool)
        instance_name = TEST_SERVER_PREFIX + "_public_ip_" + suffix
        server_id = self.__deploy_instance_helper__(instance_name=instance_name,
                                                    network_name=network_name, is_network_new=False)

        # Associate Public IP to Server
        self.nova_operations.add_floating_ip_to_instance(server_id=server_id, ip_address=allocated_ip)

    def test_deploy_instance_with_new_network_and_e2e_connection_using_public_ip(self):
        """
        Test whether it is possible to deploy an instance with new network, assign an allocated public IP
        and establish a SSH connection
        """

        self.__e2e_connection_using_public_ip_test_helper__(use_shared_network=False)

    def test_deploy_instance_with_shared_network_and_e2e_connection_using_public_ip(self):
        """
        Test whether it is possible to deploy an instance with shared network, assign an allocated public IP
        and establish a SSH connection
        """

        self.__e2e_connection_using_public_ip_test_helper__(use_shared_network=True)

    def test_deploy_instance_with_new_network_and_e2e_snat_connection(self):
        """
        Test whether it is possible to deploy an instance with new network and connect to the internet (PhoneHome)
        """

        self.__e2e_snat_connection_test_helper__(use_shared_network=False)

    def test_deploy_instance_with_shared_network_and_e2e_snat_connection(self):
        """
        Test whether it is possible to deploy an instance with shared network and connect to the internet
        """

        self.__e2e_snat_connection_test_helper__(use_shared_network=True)

    def test_deploy_instance_with_new_network_and_check_metadata_service(self):
        """
        Test whether it is possible to deploy an instance and check if metadata service is working properly (phonehome)
        """

        # skip test if suite couldn't start from an empty, clean list of allocated IPs (to avoid cascading failures)
        if self.suite_world['allocated_ips']:
            self.skipTest("There were pre-existing, not deallocated IPs")

        # skip test if no PhoneHome service endpoint was given by configuration (either in settings or by environment)
        phonehome_endpoint = self.conf[PROPERTIES_CONFIG_TEST][PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT]
        if not phonehome_endpoint:
            self.skipTest("No value found for '{}.{}' setting".format(
                PROPERTIES_CONFIG_TEST, PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT))

        path_resource = PHONEHOME_DBUS_OBJECT_METADATA_PATH
        metadata_service_url = self.conf[PROPERTIES_CONFIG_TEST][PROPERTIES_CONFIG_METADATA_SERVICE_URL]

        # Load userdata from file and compile the template (replacing variable values)
        self.logger.debug("Loading userdata from file '%s'", PHONEHOME_USERDATA_METADATA_PATH)
        with open(PHONEHOME_USERDATA_METADATA_PATH, "r") as userdata_file:
            userdata_content = userdata_file.read()
            userdata_content = replace_template_properties(userdata_content, phonehome_endpoint=phonehome_endpoint,
                                                           path_resource=path_resource,
                                                           openstack_metadata_service_url=metadata_service_url)

            self.logger.debug("Userdata content: %s", userdata_content)

        # Create Router with an external network gateway
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        router_name = TEST_ROUTER_PREFIX + "_meta_" + suffix
        external_network_id = self.__get_external_network_test_helper__()
        router_id = self.__create_router_test_helper__(router_name, external_network_id)

        # Create Network
        network_name = TEST_NETWORK_PREFIX + "_" + suffix
        network_id, subnet_id = self.__create_network_and_subnet_test_helper__(network_name)

        # Add interface to router
        port_id = self.neutron_operations.add_interface_router(router_id, subnet_id)
        self.test_world['ports'].append(port_id)

        # Create Metadata
        metadata = {"region": self.region_name, "foo": "bar-" + suffix}

        # Deploy VM
        instance_name = self.region_name.lower() + "_" + TEST_SERVER_PREFIX + "_meta_" + suffix
        server_id = self.__deploy_instance_helper__(instance_name=instance_name,
                                                    network_name=network_name, is_network_new=False,
                                                    metadata=metadata,
                                                    userdata=userdata_content)

        # VM should have this metadata associated
        expected_metadata = {'region': self.region_name, 'foo': 'bar-' + suffix}
        expected_instance_name = instance_name.replace("_", "-")

        # Create new DBus connection and wait for emitted signal from HTTP PhoneHome service
        client = DbusPhoneHomeClient(self.logger)

        result = client.connect_and_wait_for_phonehome_signal(PHONEHOME_DBUS_NAME, PHONEHOME_DBUS_OBJECT_METADATA_PATH,
                                                              PHONEHOME_METADATA_SIGNAL, expected_instance_name)

        # First, check that the DBus is registered on the system
        self.assertNotEqual(result, False, "PhoneHome bus or object not found. Please check the PhoneHome services.")

        self.assertIsNotNone(result, "PhoneHome request not received from VM '%s'" % server_id)
        self.logger.debug("Request received from VM when 'calling home': %s", result)

        # Get metadata from data received
        self.assertIn("meta", result, "PhoneHome request has been received but 'meta' param is not in")
        received_metadata = json.loads(str(result))["meta"]

        # Check metadata
        self.assertEqual(expected_metadata, received_metadata,
                         "Received metadata '%s' in PhoneHome request does not match with the expected metadata" %
                         received_metadata)
