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


from keystoneclient import session
from keystoneclient.exceptions import ClientException as KeystoneClientException
from keystoneclient.exceptions import ConnectionRefused as KeystoneConnectionRefused
from keystoneclient.exceptions import RequestTimeout as KeystoneRequestTimeout
from novaclient.exceptions import NotFound, ClientException as NovaClientException
from novaclient.exceptions import ConnectionRefused as NovaConnectionRefused
from neutronclient.common.exceptions import NeutronClientException
from swiftclient.exceptions import ClientException as SwiftClientException
from requests.exceptions import ConnectionError
from commons.nova_operations import FiwareNovaOperations
from commons.neutron_operations import FiwareNeutronOperations
from commons.swift_operations import FiwareSwiftOperations
from commons.constants import *
from ConfigParser import ConfigParser
from os.path import isfile, join
from os import environ
from os import listdir
import unittest
import urlparse
import logging
import logging.config
import time
import os
import re


class FiwareTestCase(unittest.TestCase):

    # Test configuration (to be overriden)
    conf = None

    # Test region (to be overriden)
    region_name = None

    # Test authentication
    auth_api = 'v2.0'
    auth_url = None
    auth_sess = None
    auth_token = None
    auth_cred = {}

    # Test neutron networks (could be overriden)
    with_networks = False

    # Test storage (could be overriden)
    with_storage = False

    # Test data for the suite
    suite_world = {}

    # Test logger
    logger = None

    @classmethod
    def configure(cls):
        """
        Configure the test case with values taken from `conf` read from settings file (although environment variables
        may override this configuration).
        """

        cls.logger.debug('Configuring tests for region "%s" ...', cls.region_name)

        cls.region_conf = cls.conf[PROPERTIES_CONFIG_REGION][cls.region_name]
        cls.glance_conf = cls.conf[PROPERTIES_CONFIG_TEST][PROPERTIES_CONFIG_GLANCE]

        # Check for environment variables related to credentials
        cls.auth_cred = cls.conf[PROPERTIES_CONFIG_CRED]
        env_cred = {
            PROPERTIES_CONFIG_CRED_KEYSTONE_URL:
                environ.get('OS_AUTH_URL', cls.auth_cred[PROPERTIES_CONFIG_CRED_KEYSTONE_URL]),
            PROPERTIES_CONFIG_CRED_USER:
                environ.get('OS_USERNAME', cls.auth_cred[PROPERTIES_CONFIG_CRED_USER]),
            PROPERTIES_CONFIG_CRED_PASS:
                environ.get('OS_PASSWORD', cls.auth_cred[PROPERTIES_CONFIG_CRED_PASS]),
            PROPERTIES_CONFIG_CRED_TENANT_ID:
                environ.get('OS_TENANT_ID', cls.auth_cred[PROPERTIES_CONFIG_CRED_TENANT_ID]),
            PROPERTIES_CONFIG_CRED_TENANT_NAME:
                environ.get('OS_TENANT_NAME', cls.auth_cred[PROPERTIES_CONFIG_CRED_TENANT_NAME])
        }

        # Check Identity API version from auth_url (v3 requires additional properties)
        try:
            cls.auth_url = env_cred[PROPERTIES_CONFIG_CRED_KEYSTONE_URL]
            cls.auth_api = urlparse.urlsplit(cls.auth_url).path.split('/')[1]
            if cls.auth_api == 'v3':
                domain = environ.get('OS_USER_DOMAIN_NAME', cls.auth_cred[PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME])
                env_cred.update({PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME: domain})
        except IndexError:
            assert False, "Invalid setting {}.{}".format(PROPERTIES_CONFIG_CRED, PROPERTIES_CONFIG_CRED_KEYSTONE_URL)

        # Update credentials configuration after processing environment variables
        cls.auth_cred.update(env_cred)

        # Ensure credentials are given (either by settings file or overriden by environment variables)
        for name in env_cred.keys():
            if not cls.auth_cred[name]:
                assert False, "A value for '{}.{}' setting must be provided".format(PROPERTIES_CONFIG_CRED, name)

        # Check for the rest of optional environment variables and update configuration accordingly
        default_phonehome_endpoint = cls.conf[PROPERTIES_CONFIG_TEST][PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT]
        phonehome_endpoint = environ.get('TEST_PHONEHOME_ENDPOINT', default_phonehome_endpoint)
        env_conf = {
            PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT: phonehome_endpoint
        }
        cls.conf[PROPERTIES_CONFIG_TEST].update(env_conf)

    @classmethod
    def init_auth(cls):
        """
        Init the variables related to authorization, needed to execute tests
        :return: The auth token retrieved
        """

        tenant_id = cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID]
        cred_kwargs = {
            'auth_url': cls.auth_url,
            'username': cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_USER],
            'password': cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_PASS]
        }

        # Currently, both v2 and v3 Identity API versions are supported
        if cls.auth_api == 'v2.0':
            cred_kwargs['tenant_name'] = cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_NAME]
        elif cls.auth_api == 'v3':
            cred_kwargs['user_domain_name'] = cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME]
        else:
            assert False, "Identity API {} ({}) not supported".format(cls.auth_api, cls.auth_url)

        # Instantiate a Password object
        try:
            identity_package = 'keystoneclient.auth.identity.%s' % cls.auth_api.replace('.0', '')
            identity_module = __import__(identity_package, fromlist=['Password'])
            password_class = getattr(identity_module, 'Password')
            cls.logger.debug("Authentication with %s", password_class)
            credentials = password_class(**cred_kwargs)
        except (ImportError, AttributeError) as e:
            assert False, "Could not find Identity API {} Password class: {}".format(cls.auth_api, e)

        # Get auth token
        cls.logger.debug("Getting auth token for tenant %s...", tenant_id)
        cls.auth_sess = session.Session(auth=credentials, timeout=DEFAULT_REQUEST_TIMEOUT)
        try:
            cls.auth_token = cls.auth_sess.get_token()
        except (KeystoneClientException, KeystoneConnectionRefused) as e:
            cls.logger.error("No auth token (%s): all tests will be skipped", e.message)

        return cls.auth_token

    @classmethod
    def init_clients(cls, tenant_id, test_flavor, test_image):
        """
        Init the OpenStack API clients
        """

        cls.nova_operations = FiwareNovaOperations(cls.logger, cls.region_name, test_flavor, test_image,
                                                   auth_session=cls.auth_sess)
        cls.neutron_operations = FiwareNeutronOperations(cls.logger, cls.region_name, tenant_id,
                                                         auth_session=cls.auth_sess)
        if cls.with_storage:
            cls.swift_operations = FiwareSwiftOperations(cls.logger, cls.region_name, cls.auth_api,
                                                         auth_cred=cls.auth_cred)

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
            'allocated_ips': [],
            'containers': [],
            'swift_objects': [],
            'local_objects': []
        })

        if suite:
            cls.reset_world_servers(world, suite)
            cls.reset_world_sec_groups(world, suite)
            cls.reset_world_keypair_names(world, suite)
            cls.reset_world_ports(world, suite)
            cls.reset_world_networks(world, suite)
            cls.reset_world_routers(world, suite)
            cls.reset_world_allocated_ips(world, suite)
            cls.reset_world_containers(world, suite)
            cls.reset_world_local_objects(world, suite)

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
                # Logging Nova Console-Log of the server before deleting and writing data into a new file.
                # Nova Console-Log is only retrieved when log level for Sanity Checks is set to DEBUG.
                if cls.logger_level == 'DEBUG':
                    nova_console_log = cls.nova_operations.get_nova_console_log(server_id)
                    nova_console_file_name = \
                        LOGGING_OUTPUT_NOVA_CONSOLE_LOG_TEMPLATE.format(region_name=cls.region_name.lower(),
                                                                        server_id=server_id)
                    if nova_console_log:
                        nova_console_file = open(nova_console_file_name, 'w')
                        nova_console_file.write(nova_console_log)
                        nova_console_file.close()
                        cls.logger.debug("Nova Console-Log of the server '%s' has been saved in '%s'",
                                         server_id, nova_console_file_name)
                    else:
                        cls.logger.debug("Nova Console-Log of the server '%s' is empty",
                                         server_id)

                # Deleting server
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
    def reset_world_containers(cls, world, suite=False):
        """
        Init the world['containers'] entry (after deleting existing resources)
        """
        if suite and cls.with_storage:
            # get pre-existing test containers list (ideally, empty when starting the tests)
            try:
                container_list = cls.swift_operations.list_containers(TEST_CONTAINER_PREFIX)
                for container in container_list:
                    cls.logger.debug("init_world() found container '%s' not deleted", container["name"])
                    world['containers'].append(container["name"])
            except (SwiftClientException, KeystoneConnectionRefused, KeystoneRequestTimeout, ConnectionError) as e:
                cls.logger.error("init_world() failed to get container list: %s", e)

        # release resources to ensure a clean world
        for container in list(world['containers']):
            try:
                for object in cls.swift_operations.get_container(container)[-1]:
                    cls.swift_operations.delete_object(container, object["name"])
                    try:
                        world['swift_objects'].remove(container + "/" + object["name"])
                    except ValueError:
                        cls.logger.warn("This object was removed and it came from an older execution: %s",
                                        container + "/" + object["name"])
                cls.swift_operations.delete_container(container)
                world['containers'].remove(container)
            except (SwiftClientException, KeystoneConnectionRefused, KeystoneRequestTimeout, ConnectionError) as e:
                cls.logger.error("Failed to delete container %s: %s", container, e)

    @classmethod
    def reset_world_local_objects(cls, world, suite=False):
        """
        Init the world['containers'] entry (after deleting existing resources)
        """

        local_objects_path = join(cls.home_dir, SWIFT_RESOURCES_PATH)

        if suite and cls.with_storage:
            # get pre-existing test local files list (ideally, empty when starting the tests)
            local_files = [f for f in listdir(local_objects_path) if isfile(join(local_objects_path, f))]
            for file in local_files:
                cls.logger.debug("init_world() found local object '%s' not deleted", file)
                if (file != TEST_TEXT_OBJECT_PREFIX + TEST_TEXT_FILE_EXTENSION) \
                        and (file not in list(world['local_objects'])):
                    world['local_objects'].append(file)

        # release resources to ensure a clean world
        for local_file in list(world['local_objects']):
            os.remove(join(local_objects_path, local_file))
            try:
                world['local_objects'].remove(local_file)
            except ValueError:
                cls.logger.warn("This file was removed and it came from an older execution: %s", local_file)

    @classmethod
    def setUpClass(cls):
        """
        Setup testcase (executed before ALL tests): release resources, initialize logger and REST clients.
        """

        # Initialize logger with a new custom file handler for SanityChecks using UTC time format
        config = ConfigParser()
        config.read(cls.logging_conf)
        cls.logger_level = config.get(LOGGING_CONF_SECTION_HANDLER, 'level')
        formatter = logging.Formatter(config.get(LOGGING_CONF_SECTION_FORMATTER, 'format', raw=True))
        file_handler = logging.FileHandler(config.get(LOGGING_CONF_SECTION_HANDLER, 'filename').
                                           format(region_name=cls.region_name), mode='w')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(cls.logger_level)

        logging.root.addHandler(file_handler)
        logging.Formatter.converter = time.gmtime
        cls.logger = logging.getLogger(LOGGING_TEST_LOGGER)

        # Global configuration of tests
        cls.configure()

        # Initialize session trying to get auth token; on success, continue with initialization
        tenant_id = cls.conf[PROPERTIES_CONFIG_CRED][PROPERTIES_CONFIG_CRED_TENANT_ID]
        test_image = cls.region_conf[PROPERTIES_CONFIG_REGION_TEST_IMAGE]
        test_flavor = cls.region_conf[PROPERTIES_CONFIG_REGION_TEST_FLAVOR]
        if cls.init_auth():
            cls.init_clients(tenant_id, test_flavor, test_image)
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

    def shortDescription(self):
        """
        Returns test description (even if comprising multiple lines) as a single string
        """
        return re.sub(r"\n\s*", " ", self._testMethodDoc)
