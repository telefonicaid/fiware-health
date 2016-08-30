# -*- coding: utf-8 -*-

# Copyright 2015-2016 Telefónica Investigación y Desarrollo, S.A.U
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
from commons.keystone_operations import FiwareKeystoneOperations
from commons.swift_operations import FiwareSwiftOperations
from commons.constants import *
from ConfigParser import ConfigParser
from os.path import isfile, join
from os import environ
from os import listdir
from StringIO import StringIO
import unittest
import urlparse
import logging
import logging.config
import time
import os
import re
import functools


class FiwareTestCase(unittest.TestCase):

    # Test configuration (to be overridden)
    conf = None

    # Test region (to be overridden)
    region_name = None

    # Test authentication
    auth_api = 'v2.0'
    auth_url = None
    auth_sess = None
    auth_token = None
    auth_cred = {}

    # Test neutron networks (could be overridden)
    with_networks = False

    # Test storage (could be overridden)
    with_storage = False

    # Test data for the suite
    suite_world = {}

    # Test logger
    logger = None

    # Skip message
    skip_message = None

    @classmethod
    def configure(cls):
        """
        Configure the test case with values taken from `conf` read from settings file (although environment variables
        may override this configuration).
        """

        cls.logger.debug('Configuring tests for region "%s" ...', cls.region_name)

        cls.region_conf = cls.conf[PROPERTIES_CONFIG_REGION][cls.region_name]
        cls.glance_conf = cls.conf[PROPERTIES_CONFIG_TEST][PROPERTIES_CONFIG_GLANCE]

        # Auth credentials from configuration file
        cls.auth_cred = cls.conf[PROPERTIES_CONFIG_CRED]

        # Check for environment variables overriding credentials from file
        auth_url = environ.get('OS_AUTH_URL', cls.auth_cred[PROPERTIES_CONFIG_CRED_KEYSTONE_URL])
        username = environ.get('OS_USERNAME', cls.auth_cred[PROPERTIES_CONFIG_CRED_USERNAME])
        password = environ.get('OS_PASSWORD', cls.auth_cred[PROPERTIES_CONFIG_CRED_PASSWORD])
        user_id = environ.get('OS_USER_ID', cls.auth_cred[PROPERTIES_CONFIG_CRED_USER_ID])
        tenant_id = environ.get('OS_TENANT_ID', cls.auth_cred[PROPERTIES_CONFIG_CRED_TENANT_ID])
        tenant_name = environ.get('OS_TENANT_NAME', cls.auth_cred[PROPERTIES_CONFIG_CRED_TENANT_NAME])
        usr_domain = environ.get('OS_USER_DOMAIN_NAME', cls.auth_cred[PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME])
        prj_domain = environ.get('OS_PROJECT_DOMAIN_NAME', cls.auth_cred[PROPERTIES_CONFIG_CRED_PROJECT_DOMAIN_NAME])
        environment_cred = {
            PROPERTIES_CONFIG_CRED_KEYSTONE_URL: auth_url,
            PROPERTIES_CONFIG_CRED_USERNAME: username,
            PROPERTIES_CONFIG_CRED_PASSWORD: password,
            PROPERTIES_CONFIG_CRED_USER_ID: user_id,
            PROPERTIES_CONFIG_CRED_TENANT_ID: tenant_id,
            PROPERTIES_CONFIG_CRED_TENANT_NAME: tenant_name
        }

        # Get Identity API version from auth_url (currently, both v2 and v3 are supported)
        try:
            cls.auth_url = environment_cred[PROPERTIES_CONFIG_CRED_KEYSTONE_URL]
            cls.auth_api = urlparse.urlsplit(cls.auth_url).path.split('/')[1]
            if cls.auth_api == 'v3':
                environment_cred.update({
                    PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME: usr_domain,
                    PROPERTIES_CONFIG_CRED_PROJECT_DOMAIN_NAME: prj_domain
                })
        except IndexError:
            assert False, "Invalid setting {}.{}".format(PROPERTIES_CONFIG_CRED, PROPERTIES_CONFIG_CRED_KEYSTONE_URL)

        # Update credentials configuration after processing environment variables
        cls.auth_cred.update(environment_cred)
        cls.tenant_id = cls.auth_cred[PROPERTIES_CONFIG_CRED_TENANT_ID]

        # Ensure credentials are given (either by settings file or overridden by environment variables)
        mandatory_auth_properties = environment_cred.keys()
        for name in mandatory_auth_properties:
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
        Init an auth session, needed to execute tests
        :return: The auth token retrieved
        """

        cred_kwargs = {
            'auth_url': cls.auth_url,
            'username': cls.auth_cred[PROPERTIES_CONFIG_CRED_USERNAME],
            'password': cls.auth_cred[PROPERTIES_CONFIG_CRED_PASSWORD]
        }

        # Currently, both v2 and v3 Identity API versions are supported
        if cls.auth_api == 'v2.0':
            cred_kwargs['tenant_name'] = cls.auth_cred[PROPERTIES_CONFIG_CRED_TENANT_NAME]
        elif cls.auth_api == 'v3':
            cred_kwargs['project_name'] = cls.auth_cred[PROPERTIES_CONFIG_CRED_TENANT_NAME]
            cred_kwargs['user_domain_name'] = cls.auth_cred[PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME]
            cred_kwargs['project_domain_name'] = cls.auth_cred[PROPERTIES_CONFIG_CRED_PROJECT_DOMAIN_NAME]
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
        cls.logger.debug("Getting auth token for tenant %s...", cls.tenant_id)
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
        user_id = cls.auth_cred[PROPERTIES_CONFIG_CRED_USER_ID]
        cls.nova_operations = FiwareNovaOperations(cls.logger, cls.region_name, test_flavor, test_image,
                                                   auth_session=cls.auth_sess)
        cls.neutron_operations = FiwareNeutronOperations(cls.logger, cls.region_name, tenant_id,
                                                         auth_session=cls.auth_sess)
        cls.keystone_operations = FiwareKeystoneOperations(cls.logger, cls.region_name, tenant_id,
                                                           user_id=user_id,
                                                           auth_session=cls.auth_sess,
                                                           auth_url=cls.auth_url, auth_token=cls.auth_token)
        if cls.with_storage:
            cls.swift_operations = FiwareSwiftOperations(cls.logger, cls.region_name, cls.auth_api,
                                                         auth_cred=cls.auth_cred)

    @classmethod
    def init_users(cls):
        """
        Check user for the tests and its roles
        """
        cls.user_id = cls.auth_cred[PROPERTIES_CONFIG_CRED_USER_ID]
        cls.keystone_operations.check_permitted_role()

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

        init_buffer = StringIO()
        log_handler = logging.StreamHandler(init_buffer)
        log_handler.setFormatter(cls.formatter)
        cls.logger.addHandler(log_handler)

        def _stop_capture():
            cls.logger.removeHandler(log_handler)
            log_handler.flush()
            init_buffer.flush()

        if suite:
            resets = ["cls.reset_world_servers(world, suite)",
                      "cls.reset_world_networks(world, suite)",
                      "cls.reset_world_sec_groups(world, suite)",
                      "cls.reset_world_keypair_names(world, suite)",
                      "cls.reset_world_ports(world, suite)",
                      "cls.reset_world_routers(world, suite)",
                      "cls.reset_world_allocated_ips(world, suite)",
                      "cls.reset_world_containers(world, suite)",
                      "cls.reset_world_local_objects(world, suite)"
                      ]

            def eval_reset_method(source, globals=None, locals=None):
                result = eval(source, globals, locals)
                if not result:
                    cls.logger.error("Fail with: {0}".format(source))
                return result

            results = map(functools.partial(eval_reset_method, globals=globals(), locals=locals()), resets)
            if not all(results):
                cls.logger.error("Fail in some reset_world")
                _stop_capture()
                cls._add_skip_message("Errors: {0}".format(init_buffer.getvalue()))
                return False

        _stop_capture()

        return True

    @classmethod
    def reset_world_servers(cls, world, suite=False):
        """
        Init the world['servers'] entry (after deleting existing resources)
        """
        result = True
        if suite:
            # get pre-existing server list (ideally, empty when starting the tests)
            try:
                server_list = cls.nova_operations.list_servers(TEST_SERVER_PREFIX, tenant_id=cls.tenant_id)
                for server in server_list:
                    cls.logger.debug("init_world(): found server '%s' not deleted", server.name)
                    world['servers'].append(server.id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world(), failure in Nova: failed to get server list: %s", e)
                return False

        # release resources to ensure a clean world
        for server_id in list(world['servers']):
            try:
                # Deleting server
                cls.nova_operations.delete_server(server_id)
                cls.nova_operations.wait_for_task_status(server_id, 'DELETED')
            except NotFound:
                world['servers'].remove(server_id)
                cls.logger.debug("Deleted instance %s", server_id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete server %s: %s", server_id, e)
                result = False

        # wait after server deletion process
        time.sleep(5)
        return result

    @classmethod
    def reset_world_sec_groups(cls, world, suite=False):
        """
        Init the world['sec_groups'] entry (after deleting existing resources)
        """
        result = True
        if suite:
            # get pre-existing test security group list (ideally, empty when starting the tests)
            try:
                sec_group_data_list = cls.nova_operations.list_security_groups(TEST_SEC_GROUP_PREFIX,
                                                                               tenant_id=cls.tenant_id)
                for sec_group_data in sec_group_data_list:
                    cls.logger.debug("init_world(): found security group '%s' not deleted", sec_group_data.name)
                    world['sec_groups'].append(sec_group_data.id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world(), failure in Nova: failed to get security group list: %s", e)
                return False

        # release resources to ensure a clean world
        for sec_group_id in list(world['sec_groups']):
            try:
                cls.nova_operations.delete_security_group(sec_group_id)
                world['sec_groups'].remove(sec_group_id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete security group %s: %s", sec_group_id, e)
                result = False
        return result

    @classmethod
    def reset_world_keypair_names(cls, world, suite=False):
        """
        Init the world['keypair_names'] entry (after deleting existing resources)
        """

        result = True
        if suite:
            # get pre-existing test keypair list (ideally, empty when starting the tests)
            try:
                keypair_list = cls.nova_operations.list_keypairs(TEST_KEYPAIR_PREFIX)
                for keypair in keypair_list:
                    cls.logger.debug("init_world(): found keypair '%s' not deleted", keypair.name)
                    world['keypair_names'].append(keypair.name)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world(), failure in Nova: failed to get keypair list: %s", e)
                return False

        # release resources to ensure a clean world
        for keypair_name in list(world['keypair_names']):
            try:
                cls.nova_operations.delete_keypair(keypair_name)
                world['keypair_names'].remove(keypair_name)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete keypair %s: %s", keypair_name, e)
                result = False
        return result

    @classmethod
    def reset_world_networks(cls, world, suite=False):
        """
        Init the world['networks'] entry (after deleting existing resources)
        """
        result = True

        if suite and cls.with_networks:
            # get pre-existing test network list (ideally, empty when starting the tests)
            try:
                network_list = cls.neutron_operations.list_networks(TEST_NETWORK_PREFIX)
                for network in network_list:
                    cls.logger.debug("init_world() found network '%s' not deleted", network['name'])
                    world['networks'].append(network['id'])
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world(), failure in Neutron: failed to get network list: %s", e)
                return False

        # release resources to ensure a clean world
        for network_id in list(world['networks']):
            try:
                cls.neutron_operations.delete_network(network_id)
                world['networks'].remove(network_id)
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete network %s: %s", network_id, e)
                result = False

        return result

    @classmethod
    def reset_world_routers(cls, world, suite=False):
        """
        Init the world['routers'] entry (after deleting existing resources)
        """
        result = True
        if suite and cls.with_networks:
            # get pre-existing test router list (ideally, empty when starting the tests)
            try:
                router_list = cls.neutron_operations.list_routers(TEST_ROUTER_PREFIX)
                for router in router_list:
                    cls.logger.debug("init_world(): found router '%s' not deleted", router['name'])
                    world['routers'].append(router['id'])
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world(), failure in Neutron: failed to get router list: %s", e)
                return False

        # release resources to ensure a clean world
        for router_id in list(world['routers']):
            try:
                cls.neutron_operations.delete_router(router_id)
                world['routers'].remove(router_id)
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete router %s: %s", router_id, e)
                result = False
        return result

    @classmethod
    def reset_world_allocated_ips(cls, world, suite=False):
        """
        Init the world['allocated_ips'] entry (after deallocating existing resources)
        """
        result = True
        if suite:
            # get pre-existing allocated IP list (ideally, empty when starting the tests)
            try:
                ip_data_list = cls.nova_operations.list_allocated_ips()
                for ip_data in ip_data_list:
                    cls.logger.debug("init_world(): found IP %s not deallocated", ip_data.ip)
                    world['allocated_ips'].append(ip_data.id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world(), failure in Nova: failed to get allocated IP list: %s", e)
                return False

        # release resources to ensure a clean world
        for allocated_ip_id in list(world['allocated_ips']):
            try:
                cls.nova_operations.deallocate_ip(allocated_ip_id)
                world['allocated_ips'].remove(allocated_ip_id)
            except (NovaClientException, NovaConnectionRefused, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to deallocate IP %s: %s", allocated_ip_id, e)
                result = False

        return result

    @classmethod
    def reset_world_ports(cls, world, suite=False):
        """
        Init the world['ports'] entry (after deleting existing resources)
        """
        result = True
        if suite and cls.with_networks:
            # get pre-existing port list (ideally, empty when starting the tests)
            try:
                port_list = cls.neutron_operations.list_ports()
                for port in port_list:
                    cls.logger.debug("init_world(): found port '%s' not deleted", port['id'])
                    world['ports'].append(port)
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("init_world(), failure in Neutron: failed to get port list: %s", e)
                return False

        # release resources to ensure a clean test_world

        for port in world['ports']:
            if isinstance(port, unicode):
                world['ports'].remove(port)
                port = cls.neutron_operations.show_port(port)
            try:
                if port.get("tenant_id") != cls.tenant_id or port.get("device_owner") == 'compute:None':
                    continue
                port_data = cls.neutron_operations.show_port(port.get('id'))
                if 'network:router_interface' in port_data['device_owner']:
                    for fixed_ip in port_data['fixed_ips']:
                        cls.neutron_operations.delete_interface_router(router_id=port_data['device_id'],
                                                                       subnetwork_id=fixed_ip['subnet_id'])
                else:
                    cls.neutron_operations.delete_port(port['id'])
                if port in world['ports']:
                    world['ports'].remove(port)
            except (NeutronClientException, KeystoneConnectionRefused, KeystoneRequestTimeout) as e:
                cls.logger.error("Failed to delete port %s: %s", port['id'], e)
                result = False
        return result

    @classmethod
    def reset_world_containers(cls, world, suite=False):
        """
        Init the world['containers'] entry (after deleting existing resources)
        """
        result = True
        if suite and cls.with_storage:
            # get pre-existing test containers list (ideally, empty when starting the tests)
            try:
                container_list = cls.swift_operations.list_containers(TEST_CONTAINER_PREFIX)
                for container in container_list:
                    cls.logger.debug("init_world(): found container '%s' not deleted", container["name"])
                    world['containers'].append(container["name"])
            except (SwiftClientException, KeystoneConnectionRefused, KeystoneRequestTimeout, ConnectionError) as e:
                cls.logger.error("init_world(), failure in Swift: failed to get container list: %s", e)
                return False

        # release resources to ensure a clean world
        for container in list(world['containers']):
            try:
                for object in cls.swift_operations.get_container(container)[-1]:
                    cls.swift_operations.delete_object(container, object["name"])
                    try:
                        world['swift_objects'].remove(container + "/" + object["name"])
                    except ValueError:
                        cls.logger.warn("This object was removed and it came from a previous execution: %s",
                                        container + "/" + object["name"])
                cls.swift_operations.delete_container(container)
                world['containers'].remove(container)
            except (SwiftClientException, KeystoneConnectionRefused, KeystoneRequestTimeout, ConnectionError) as e:
                cls.logger.error("Failed to delete container %s: %s", container, e)
                result = False
        return result

    @classmethod
    def reset_world_local_objects(cls, world, suite=False):
        """
        Init the world['containers'] entry (after deleting existing resources)
        """
        result = True
        local_objects_path = join(cls.home_dir, SWIFT_TMP_RESOURCES_PATH)

        if suite and cls.with_storage:
            # get pre-existing test local files list (ideally, empty when starting the tests)
            local_files = [f for f in listdir(local_objects_path) if isfile(join(local_objects_path, f))]
            for file in local_files:
                cls.logger.debug("init_world() found local object '%s' not deleted", file)
                if file.startswith(cls.region_name) and file not in list(world['local_objects']):
                    world['local_objects'].append(file)

        # release resources to ensure a clean world
        for local_file in list(world['local_objects']):
            os.remove(join(local_objects_path, local_file))
            try:
                world['local_objects'].remove(local_file)
            except ValueError:
                cls.logger.warn("This file was removed and it came from a previous execution: %s", local_file)

        return result

    @classmethod
    def setUpClass(cls):
        """
        Setup testcase (executed before ALL tests): release resources, initialize logger and REST clients.
        """

        try:

            # Initialize logger with a new custom file handler for SanityChecks using UTC time format
            config = ConfigParser()
            config.read(cls.logging_conf)
            cls.logger_level = config.get(LOGGING_CONF_SECTION_HANDLER, 'level')
            cls.formatter = logging.Formatter(config.get(LOGGING_CONF_SECTION_FORMATTER, 'format', raw=True))
            file_handler = logging.FileHandler(config.get(LOGGING_CONF_SECTION_HANDLER, 'filename').
                                               format(region_name=cls.region_name), mode='w')
            file_handler.setFormatter(cls.formatter)
            file_handler.setLevel(cls.logger_level)

            logging.root.addHandler(file_handler)
            logging.Formatter.converter = time.gmtime
            cls.logger = logging.getLogger(LOGGING_TEST_LOGGER)

            # Global configuration of tests
            cls.configure()

            # Initialize session trying to get auth token; on success, continue with initialization
            test_image = cls.region_conf.get(PROPERTIES_CONFIG_REGION_TEST_IMAGE, TEST_IMAGE_DEFAULT)
            test_flavor = cls.region_conf.get(PROPERTIES_CONFIG_REGION_TEST_FLAVOR, TEST_FLAVOR_DEFAULT)
            if cls.init_auth():
                cls.init_clients(cls.tenant_id, test_flavor, test_image)
                cls.init_users()
                if not cls.init_world(cls.suite_world, suite=True):
                    raise Exception("Error in initialization phase: resources from previous executions not released")
                cls.logger.debug("suite_world = %s", cls.suite_world)
        except Exception as ex:
            cls.logger.error("Error in initialization phase: %s", ex.message)
            cls._add_skip_message("Error in initialization phase: {0}".format(ex.message))

    @classmethod
    def _add_skip_message(cls, message):
        """
        Build a message with all traces in case of skip test
        :param message: new line to add
        """
        if cls.skip_message:
            cls.skip_message = "{0}\n{1}".format(cls.skip_message, message)
        else:
            cls.skip_message = message

    @classmethod
    def tearDownClass(cls):
        None

    def setUp(self):
        """
        Setup each single test
        """
        if self.skip_message:
            self.skipTest(self.skip_message)

        # skip test if no auth token could be retrieved
        if not self.auth_token:
            self.skipTest("No auth token could be retrieved")

    def shortDescription(self):
        """
        Returns test description (even if comprising multiple lines) as a single string
        """
        return re.sub(r"\n\s*", " ", self._testMethodDoc)
