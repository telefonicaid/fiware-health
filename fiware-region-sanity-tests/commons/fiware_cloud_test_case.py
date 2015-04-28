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


from keystoneclient import auth, session
from keystoneclient.exceptions import ClientException as KeystoneClientException
from keystoneclient.exceptions import ConnectionRefused as KeystoneConnectionRefused
from keystoneclient.exceptions import RequestTimeout as KeystoneRequestTimeout
from novaclient.exceptions import NotFound, ClientException as NovaClientException
from novaclient.exceptions import ConnectionRefused as NovaConnectionRefused
from neutronclient.common.exceptions import NeutronClientException
from commons.nova_operations import FiwareNovaOperations
from commons.neutron_operations import FiwareNeutronOperations
from commons.swift_operations import FiwareSwiftOperations
from commons.constants import *
from os import environ
import unittest
import logging
import json
import time


class FiwareTestCase(unittest.TestCase):

    # Test region (to be overriden)
    region_name = None

    # Test authentication
    auth_url = None
    auth_sess = None
    auth_token = None

    # Test neutron networks (could be overriden)
    with_networks = True

    # Test data for the suite
    suite_world = {}

    # Test logger
    logger = None

    @classmethod
    def load_project_properties(cls):
        """
        Parse the JSON configuration file located in the settings folder and store the resulting dictionary in the
        `conf` class variable. Values from "standard" OpenStack environment variables override this configuration.
        """

        cls.logger.debug("Loading test settings...")
        with open(PROPERTIES_FILE) as config_file:
            try:
                cls.conf = json.load(config_file)
            except Exception as e:
                assert False, "Error parsing config file '{}': {}".format(PROPERTIES_FILE, e)

        # Check for environment variables related to credentials and update configuration
        cred = cls.conf[PROPERTIES_CONFIG_CRED]
        env_cred = {
            PROPERTIES_CONFIG_CRED_KEYSTONE_URL: environ.get('OS_AUTH_URL', cred[PROPERTIES_CONFIG_CRED_KEYSTONE_URL]),
            PROPERTIES_CONFIG_CRED_USER: environ.get('OS_USERNAME', cred[PROPERTIES_CONFIG_CRED_USER]),
            PROPERTIES_CONFIG_CRED_PASS: environ.get('OS_PASSWORD', cred[PROPERTIES_CONFIG_CRED_PASS]),
            PROPERTIES_CONFIG_CRED_TENANT_ID: environ.get('OS_TENANT_ID', cred[PROPERTIES_CONFIG_CRED_TENANT_ID]),
            PROPERTIES_CONFIG_CRED_TENANT_NAME: environ.get('OS_TENANT_NAME', cred[PROPERTIES_CONFIG_CRED_TENANT_NAME])
        }
        cred.update(env_cred)

        # Check for optional environment variables related to test configuration and update configuration
        conf = cls.conf[PROPERTIES_CONFIG_TEST]
        phonehome_endpoint = environ.get('TEST_PHONEHOME_ENDPOINT', conf[PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT])
        env_conf = {
            PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT: phonehome_endpoint
        }
        conf.update(env_conf)

        # Ensure credentials are given (either by settings file or overriden by environment variables)
        for name in env_cred.keys():
            if not cred[name]:
                assert False, "A value for '{}.{}' setting must be provided".format(PROPERTIES_CONFIG_CRED, name)

    @classmethod
    def init_auth(cls):
        """
        Init the variables related to authorization, needed to execute tests
        :return: The auth token retrieved
        """

        tenant_id = cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID]
        cls.credentials = auth.identity.v2.Password(
            auth_url=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_KEYSTONE_URL],
            username=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_USER],
            password=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_PASS],
            tenant_name=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_NAME])

        cls.logger.debug("Getting auth token for tenant %s...", tenant_id)
        cls.auth_url = cls.credentials.auth_url
        cls.auth_sess = session.Session(auth=cls.credentials, timeout=DEFAULT_REQUEST_TIMEOUT)
        try:
            cls.auth_token = cls.auth_sess.get_token()
        except (KeystoneClientException, KeystoneConnectionRefused) as e:
            cls.logger.error("No auth token (%s): all tests will be skipped", e.message)

        return cls.auth_token

    @classmethod
    def init_clients(cls, tenant_id, test_flavor):
        """
        Init the OpenStack API clients
        """

        cls.nova_operations = FiwareNovaOperations(cls.logger, cls.region_name, test_flavor,
                                                   auth_session=cls.auth_sess)
        cls.neutron_operations = FiwareNeutronOperations(cls.logger, cls.region_name, tenant_id,
                                                         auth_session=cls.auth_sess)
        cls.swift_operations = FiwareSwiftOperations(cls.logger, cls.region_name, cred=cls.credentials,
                                                         auth_session=cls.auth_sess)

    @classmethod
    def init_world(cls, world, suite=False):
        """
        Init the `world` variable to store created data by tests
        """

        world.update({
            'servers': [],
            'sec_groups': [],
            'keypair_names': [],
            'ports': [],
            'networks': [],
            'routers': [],
            'allocated_ips': []
        })

        if suite:
            cls.reset_world_servers(world, suite)
            cls.reset_world_sec_groups(world, suite)
            cls.reset_world_keypair_names(world, suite)
            cls.reset_world_ports(world, suite)
            cls.reset_world_networks(world, suite)
            cls.reset_world_routers(world, suite)
            cls.reset_world_allocated_ips(world, suite)

    @classmethod
    def reset_world_servers(cls, world, suite=False):
        """
        Init the world['servers'] entry (after deleting existing resources)
        """

        if suite:
            # get pre-existing server list (ideally, empty when starting the tests)
            try:
                server_list = cls.nova_operations.list_servers(TEST_SERVER_PREFIX)
                for server in server_list:
                    cls.logger.debug("init_world() found server '%s' not deleted", server.name)
                    world['servers'].append(server.id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world() failed to get server list: %s", e)

        # release resources to ensure a clean world
        for server_id in list(world['servers']):
            try:
                cls.nova_operations.delete_server(server_id)
                cls.nova_operations.wait_for_task_status(server_id, 'DELETED')
            except NotFound:
                world['servers'].remove(server_id)
                cls.logger.debug("Deleted instance %s", server_id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete server %s: %s", server_id, e)

        # wait after server deletion process
        time.sleep(5)

    @classmethod
    def reset_world_sec_groups(cls, world, suite=False):
        """
        Init the world['sec_groups'] entry (after deleting existing resources)
        """

        if suite:
            # get pre-existing test security group list (ideally, empty when starting the tests)
            try:
                sec_group_data_list = cls.nova_operations.list_security_groups(TEST_SEC_GROUP_PREFIX)
                for sec_group_data in sec_group_data_list:
                    cls.logger.debug("init_world() found security group '%s' not deleted", sec_group_data.name)
                    world['sec_groups'].append(sec_group_data.id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world() failed to get security group list: %s", e)

        # release resources to ensure a clean world
        for sec_group_id in list(world['sec_groups']):
            try:
                cls.nova_operations.delete_security_group(sec_group_id)
                world['sec_groups'].remove(sec_group_id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete security group %s: %s", sec_group_id, e)

    @classmethod
    def reset_world_keypair_names(cls, world, suite=False):
        """
        Init the world['keypair_names'] entry (after deleting existing resources)
        """

        if suite:
            # get pre-existing test keypair list (ideally, empty when starting the tests)
            try:
                keypair_list = cls.nova_operations.list_keypairs(TEST_KEYPAIR_PREFIX)
                for keypair in keypair_list:
                    cls.logger.debug("init_world() found keypair '%s' not deleted", keypair.name)
                    world['keypair_names'].append(keypair.name)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world() failed to get keypair list: %s", e)

        # release resources to ensure a clean world
        for keypair_name in list(world['keypair_names']):
            try:
                cls.nova_operations.delete_keypair(keypair_name)
                world['keypair_names'].remove(keypair_name)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete keypair %s: %s", keypair_name, e)

    @classmethod
    def reset_world_networks(cls, world, suite=False):
        """
        Init the world['networks'] entry (after deleting existing resources)
        """

        if suite and cls.with_networks:
            # get pre-existing test network list (ideally, empty when starting the tests)
            try:
                network_list = cls.neutron_operations.list_networks(TEST_NETWORK_PREFIX)
                for network in network_list:
                    cls.logger.debug("init_world() found network '%s' not deleted", network['name'])
                    world['networks'].append(network['id'])
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world() failed to get network list: %s", e)

        # release resources to ensure a clean world
        for network_id in list(world['networks']):
            try:
                cls.neutron_operations.delete_network(network_id)
                world['networks'].remove(network_id)
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete network %s: %s", network_id, e)

    @classmethod
    def reset_world_routers(cls, world, suite=False):
        """
        Init the world['routers'] entry (after deleting existing resources)
        """

        if suite and cls.with_networks:
            # get pre-existing test router list (ideally, empty when starting the tests)
            try:
                router_list = cls.neutron_operations.list_routers(TEST_ROUTER_PREFIX)
                for router in router_list:
                    cls.logger.debug("init_world() found router '%s' not deleted", router['name'])
                    world['routers'].append(router['id'])
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world() failed to get router list: %s", e)

        # release resources to ensure a clean world
        for router_id in list(world['routers']):
            try:
                cls.neutron_operations.delete_router(router_id)
                world['routers'].remove(router_id)
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete router %s: %s", router_id, e)

    @classmethod
    def reset_world_allocated_ips(cls, world, suite=False):
        """
        Init the world['allocated_ips'] entry (after deallocating existing resources)
        """

        if suite:
            # get pre-existing allocated IP list (ideally, empty when starting the tests)
            try:
                ip_data_list = cls.nova_operations.list_allocated_ips()
                for ip_data in ip_data_list:
                    cls.logger.debug("init_world() found IP %s not deallocated", ip_data.ip)
                    world['allocated_ips'].append(ip_data.id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world() failed to get allocated IP list: %s", e)

        # release resources to ensure a clean world
        for allocated_ip_id in list(world['allocated_ips']):
            try:
                cls.nova_operations.deallocate_ip(allocated_ip_id)
                world['allocated_ips'].remove(allocated_ip_id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to deallocate IP %s: %s", allocated_ip_id, e)

    @classmethod
    def reset_world_ports(cls, world, suite=False):
        """
        Init the world['ports'] entry (after deleting existing resources)
        """

        if suite and cls.with_networks:
            # get pre-existing port list (ideally, empty when starting the tests)
            try:
                port_list = cls.neutron_operations.list_ports()
                for port in port_list:
                    cls.logger.debug("init_world() found port '%s' not deleted", port['id'])
                    world['ports'].append(port['id'])
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world() failed to get port list: %s", e)

        # release resources to ensure a clean test_world
        for port_id in list(world['ports']):
            try:
                port_data = cls.neutron_operations.show_port(port_id)
                if 'network:router_interface' in port_data['device_owner']:
                    for fixed_ip in port_data['fixed_ips']:
                        cls.neutron_operations.delete_interface_router(router_id=port_data['device_id'],
                                                                       subnetwork_id=fixed_ip['subnet_id'])
                else:
                    cls.neutron_operations.delete_port(port_id)
                world['ports'].remove(port_id)
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete port %s: %s", port_id, e)

    @classmethod
    def setUpClass(cls):
        """
        Setup testcase (executed before ALL tests): release resources, initialize logger and REST clients.
        """

        # Initialize logger
        cls.logger = logging.getLogger(PROPERTIES_LOGGER)

        # These tests should be particularized for a region
        cls.logger.debug("Tests for '%s' region", cls.region_name)

        # Get properties from global config
        tenant_id = cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID]
        test_flavor = cls.conf[PROPERTIES_CONFIG_REGION][PROPERTIES_CONFIG_REGION_TEST_FLAVOR].get(cls.region_name)

        # Initialize session trying to get auth token; on success, continue with initialization
        if cls.init_auth():
            cls.init_clients(tenant_id, test_flavor)
            cls.init_world(cls.suite_world, suite=True)
            cls.logger.debug("suite_world = %s", cls.suite_world)

    @classmethod
    def tearDownClass(cls):
        None

    def setUp(self):
        """
        Setup each single test
        """

        # skip test if no auth token could be retrieved
        if not self.auth_token:
            self.skipTest("No auth token could be retrieved")
