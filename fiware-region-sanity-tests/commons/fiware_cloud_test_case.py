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
from keystoneclient.openstack.common.apiclient.exceptions import ClientException as KeystoneClientException
from novaclient.exceptions import NotFound, ClientException as NovaClientException
from neutronclient.common.exceptions import NeutronClientException
from commons.nova_operations import FiwareNovaOperations
from commons.neutron_operations import FiwareNeutronOperations
from commons.constants import *
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

    # Temporal test data
    test_world = {}

    # Test logger
    logger = None

    @classmethod
    def load_project_properties(cls):
        """
        Parse the JSON configuration file located in the settings folder and
        store the resulting dictionary in the config class variable.
        """

        cls.logger.debug("Loading test settings...")
        with open(PROPERTIES_FILE) as config_file:
            try:
                cls.conf = json.load(config_file)
            except Exception as e:
                assert False, "Error parsing config file '{}': {}".format(PROPERTIES_FILE, e)

        for name in [PROPERTIES_CONFIG_CRED_USER, PROPERTIES_CONFIG_CRED_PASS, PROPERTIES_CONFIG_CRED_TENANT_ID]:
            if not cls.conf[PROPERTIES_CONFIG_CRED][name]:
                assert False, "A value for '{}' must be provided in config file '{}'".format(name, PROPERTIES_FILE)

    @classmethod
    def init_auth(cls):
        """
        Init the variables related to authorization, needed to execute tests
        :return: The auth token retrieved
        """

        credentials = auth.identity.v2.Password(
            auth_url=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_KEYSTONE_URL],
            username=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_USER],
            password=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_PASS],
            tenant_name=cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID])

        cls.logger.debug("Getting auth token...")
        cls.auth_url = credentials.auth_url
        cls.auth_sess = session.Session(auth=credentials)
        try:
            cls.auth_token = cls.auth_sess.get_token()
        except KeystoneClientException as e:
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

    @classmethod
    def init_world(cls):
        """
        Init the test_world variable to store created data by tests
        """

        cls.test_world.update({
            'servers': [],
            'sec_groups': [],
            'keypair_names': [],
            'networks': [],
            'routers': [],
            'allocated_ips': []
        })

        cls.reset_world_servers(init=True)
        cls.reset_world_sec_groups(init=True)
        cls.reset_world_keypair_names(init=True)
        cls.reset_world_networks(init=True)
        cls.reset_world_routers(init=True)
        cls.reset_world_allocated_ips(init=True)
        cls.logger.debug("test_world = %s", str(cls.test_world))

    @classmethod
    def reset_world_servers(cls, init=False):
        """
        Init the test_world['servers'] entry (possibly, after deleting resources)
        """

        if init:
            # get pre-existing server list (ideally, empty when starting the tests)
            try:
                server_list = cls.nova_operations.list_servers()
                for server in server_list:
                    cls.logger.debug("init_world() found server '%s' not deleted", server.name)
                    cls.test_world['servers'].append(server.id)
            except NovaClientException as e:
                cls.logger.error("init_world() failed to get server list: %s", e)

        # release resources to ensure a clean test_world
        for server_id in list(cls.test_world['servers']):
            try:
                cls.nova_operations.delete_server(server_id)
                cls.nova_operations.wait_for_task_status(server_id, 'DELETED')
            except NotFound:
                cls.test_world['servers'].remove(server_id)
                cls.logger.debug("Deleted instance %s", server_id)
            except NovaClientException as e:
                cls.logger.error("Failed to delete server %s: %s", server_id, e)

        # wait after server deletion process
        time.sleep(5)

    @classmethod
    def reset_world_sec_groups(cls, init=False):
        """
        Init the test_world['sec_groups'] entry (possibly, after deleting resources)
        """

        if init:
            # get pre-existing test security group list (ideally, empty when starting the tests)
            try:
                sec_group_data_list = cls.nova_operations.list_security_groups(TEST_SEC_GROUP_PREFIX)
                for sec_group_data in sec_group_data_list:
                    cls.logger.debug("init_world() found security group '%s' not deleted", sec_group_data.name)
                    cls.test_world['sec_groups'].append(sec_group_data.id)
            except NovaClientException as e:
                cls.logger.error("init_world() failed to get security group list: %s", e)

        # release resources to ensure a clean test_world
        for sec_group_id in list(cls.test_world['sec_groups']):
            try:
                cls.nova_operations.delete_security_group(sec_group_id)
                cls.test_world['sec_groups'].remove(sec_group_id)
            except NovaClientException as e:
                cls.logger.error("Failed to delete security group %s: %s", sec_group_id, e)

    @classmethod
    def reset_world_keypair_names(cls, init=False):
        """
        Init the test_world['keypair_names'] entry (possibly, after deleting resources)
        """

        if init:
            # get pre-existing test keypair list (ideally, empty when starting the tests)
            try:
                keypair_list = cls.nova_operations.list_keypairs(TEST_KEYPAIR_PREFIX)
                for keypair in keypair_list:
                    cls.logger.debug("init_world() found keypair '%s' not deleted", keypair.name)
                    cls.test_world['keypair_names'].append(keypair.name)
            except NovaClientException as e:
                cls.logger.error("init_world() failed to get keypair list: %s", e)

        # release resources to ensure a clean test_world
        for keypair_name in list(cls.test_world['keypair_names']):
            try:
                cls.nova_operations.delete_keypair(keypair_name)
                cls.test_world['keypair_names'].remove(keypair_name)
            except NovaClientException as e:
                cls.logger.error("Failed to delete keypair %s: %s", keypair_name, e)

    @classmethod
    def reset_world_networks(cls, init=False):
        """
        Init the test_world['networks'] entry (possibly, after deleting resources)
        """

        if init:
            # get pre-existing test network list (ideally, empty when starting the tests)
            try:
                network_list = cls.neutron_operations.list_networks(TEST_NETWORK_PREFIX)
                for network in network_list:
                    cls.logger.debug("init_world() found network '%s' not deleted", network['name'])
                    cls.test_world['networks'].append(network['id'])
            except NeutronClientException as e:
                cls.logger.error("init_world() failed to get network list: %s", e)

        # release resources to ensure a clean test_world
        for network_id in list(cls.test_world['networks']):
            try:
                cls.neutron_operations.delete_network(network_id)
                cls.test_world['networks'].remove(network_id)
            except NeutronClientException as e:
                cls.logger.error("Failed to delete network %s: %s", network_id, e)

    @classmethod
    def reset_world_routers(cls, init=False):
        """
        Init the test_world['routers'] entry (possibly, after deleting resources)
        """

        if init:
            # get pre-existing test router list (ideally, empty when starting the tests)
            try:
                router_list = cls.neutron_operations.list_routers(TEST_ROUTER_PREFIX)
                for router in router_list:
                    cls.logger.debug("init_world() found router '%s' not deleted", router['name'])
                    cls.test_world['routers'].append(router['id'])
            except NeutronClientException as e:
                cls.logger.error("init_world() failed to get router list: %s", e)

        # release resources to ensure a clean test_world
        for router_id in list(cls.test_world['routers']):
            try:
                cls.neutron_operations.delete_router(router_id)
                cls.test_world['routers'].remove(router_id)
            except NeutronClientException as e:
                cls.logger.error("Failed to delete router %s: %s", router_id, e)

    @classmethod
    def reset_world_allocated_ips(cls, init=False):
        """
        Init the test_world['allocated_ips'] entry (possibly, after deallocating resources)
        """

        if init:
            # get pre-existing allocated IP list (ideally, empty when starting the tests)
            try:
                ip_data_list = cls.nova_operations.list_allocated_ips()
                for ip_data in ip_data_list:
                    cls.logger.debug("init_world() found IP %s not deallocated", ip_data.ip)
                    cls.test_world['allocated_ips'].append(ip_data.id)
            except NovaClientException as e:
                cls.logger.error("init_world() failed to get allocated IP list: %s", e)

        # release resources to ensure a clean test_world
        for allocated_ip_id in list(cls.test_world['allocated_ips']):
            try:
                cls.nova_operations.deallocate_ip(allocated_ip_id)
                cls.test_world['allocated_ips'].remove(allocated_ip_id)
            except NovaClientException as e:
                cls.logger.error("Failed to deallocate IP %s: %s", allocated_ip_id, e)

    @classmethod
    def setUpClass(cls):
        """
        Setup testcase (executed before ALL tests): initialize logger and REST-Clients.
        """

        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        cls.logger = logging.getLogger("TestCase")
        cls.logger.addHandler(handler)
        cls.logger.setLevel(logging.NOTSET)

        # These tests should be particularized for a region
        cls.logger.debug("Tests for '%s' region", cls.region_name)

        # Load properties from config file
        cls.load_project_properties()
        username = cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_USER]
        tenant_id = cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID]
        test_flavor = cls.conf[PROPERTIES_CONFIG_REGION][PROPERTIES_CONFIG_REGION_TEST_FLAVOR].get(cls.region_name)
        cls.logger.debug("Settings = {'user': '%s', 'tenant': '%s'}", username, tenant_id)

        # Initialize session trying to get auth token; on success, continue with initialization
        if cls.init_auth():
            cls.init_clients(tenant_id, test_flavor)
            cls.init_world()

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
