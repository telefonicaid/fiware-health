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


from novaclient.v1_1 import client
from commons.constants import DEFAULT_REQUEST_TIMEOUT, SLEEP_TIME, MAX_WAIT_ITERATIONS, TEST_FLAVOR_DEFAULT, \
    SSH_CONNECTION_PORT
import time
import re


class FiwareNovaOperations:

    def __init__(self, logger, region_name, test_flavor, **kwargs):
        """
        Initializes Nova-Client.
        :param logger: Logger object
        :param region_name: Fiware Region name
        :param test_flavor: Flavor for new test instances
        :param auth_session: Keystone auth session object
        :param auth_url: Keystone auth URL (needed if no session is given)
        :param auth_token: Keystone auth token (needed if no session is given)
        """

        self.logger = logger
        self.test_flavor_regex = re.compile("(.+\.)?%s$" % (test_flavor or TEST_FLAVOR_DEFAULT))
        self.client = client.Client(session=kwargs.get('auth_session'),
                                    auth_url=kwargs.get('auth_url'), auth_token=kwargs.get('auth_token'),
                                    endpoint_type='publicURL', service_type="compute",
                                    region_name=region_name,
                                    timeout=DEFAULT_REQUEST_TIMEOUT)

    def get_flavor_list(self):
        """
        Gets the list of flavors.
        :return: A list of :class:`Flavor`
        """
        flavor_list = self.client.flavors.list()
        return flavor_list

    def get_any_flavor_id(self):
        """
        Gets a flavor id from the available ones (preferably that matching default test flavor, otherwise the last one)
        :return: Flavor ID, or None if no flavors were available
        """
        flavor_id = None
        flavor_list = self.get_flavor_list()
        for flavor in flavor_list:
            flavor_id = flavor.id
            if self.test_flavor_regex.match(flavor.name):
                break
        return flavor_id

    def get_image_list(self):
        """
        Gets the list of images.
        :return: A list of :class:`Image`
        """
        image_list = self.client.images.list()
        return image_list

    def get_any_image_id(self):
        """
        Gets a image id from the available ones (first with 'init' in its name)
        :return: Image ID, or None if not found
        """
        image_id = None
        image_list = self.get_image_list()
        for image in image_list:
            if 'init' in image.name:
                image_id = image.id
                break
        return image_id

    def find_image_id_by_name(self, image_name):
        """
        Finds an image by name
        :param image_name: Name of the image
        :return: Id of first image that matches the given name
        """
        nova_img_list = self.client.images.findall(name=image_name)
        if len(nova_img_list) != 0:
            return nova_img_list[0].id
        else:
            return None

    def create_security_group_and_rules(self, name):
        """
        Creates a new Security Group and a default Rule (TCP/22)
        :param name: Name of Sec. Group.
        :return: Security Group ID
        """

        # new security group
        sec_group = self.client.security_groups.create(name, "Testing purpose")
        self.logger.debug("Created security group '%s': %s", name, sec_group.id)

        # new rule in security group (by default)
        cidr = "0.0.0.0/0"
        protocol = "TCP"
        port = SSH_CONNECTION_PORT
        sec_group_rule = self.client.security_group_rules.create(sec_group.id, ip_protocol=protocol,
                                                                 from_port=port, to_port=port, cidr=cidr)
        self.logger.debug("Created security group rule (%s %d %s): %s", protocol, port, cidr, sec_group_rule)

        return sec_group.id

    def delete_security_group(self, sec_group_id):
        """
        Removes the Sec. Group.
        :param sec_group_id: Sec. Group to be deleted.
        :return: None
        """
        self.client.security_groups.delete(sec_group_id)
        self.logger.debug("Deleted security group %s", sec_group_id)

    def list_security_groups(self, name_prefix=None):
        """
        Gets all the security groups
        :param name_prefix: Prefix to match security group names
        :return: A list of :class:`SecurityGroup`
        """
        sec_group_list = self.client.security_groups.list()
        if name_prefix:
            sec_group_list = [sec_group for sec_group in sec_group_list if sec_group.name.startswith(name_prefix)]

        return sec_group_list

    def create_keypair(self, name):
        """
        Creates new Keypair.
        :param name: Name of the Keypair
        :return: Private Key generated.
        """
        nova_keypair = self.client.keypairs.create(name)
        self.logger.debug("Created keypair %s", nova_keypair.name)
        return nova_keypair.private_key

    def delete_keypair(self, name):
        """
        Removes a Keypair.
        :param name: Name of the keypair to be deleted.
        :return: None
        """
        keypair = self.client.keypairs.find(name=name)
        self.client.keypairs.delete(keypair)
        self.logger.debug("Deleted keypair '%s'", name)

    def list_keypairs(self, name_prefix=None):
        """
        Gets all the keypairs
        :param name_prefix: Prefix to match keypair names
        :return: A list of :class:`Keypair`
        """
        keypair_list = self.client.keypairs.list()
        if name_prefix:
            keypair_list = [keypair for keypair in keypair_list if keypair.name.startswith(name_prefix)]

        return keypair_list

    def find_keypair(self, **kwargs):
        """
        Gets the keypairs matching attributes given in `kwargs`.
        :return: A a keypair data :class:`Keypair` that matches with the giver params
        """
        keypair_list = self.client.keypairs.find(**kwargs)
        self.logger.debug("Find keypairs by %s. Result: %s", str(kwargs.items()), str(keypair_list))
        return keypair_list

    def launch_instance(self, instance_name, image_id, flavor_id, keypair_name=None, metadata=None, userdata=None,
                        security_group_name_list=None, network_id_list=None):
        """
        Launches a new Service Instance.
        :param instance_name: Something to name the server.
        :param image_id: The ImageID to boot with.
        :param flavor_id: The FlavorID to boot onto.
        :param keypair_name: (optional extension) name of previously created
                      keypair to inject into the instance.
        :param metadata:  A dict of arbitrary key/value metadata to store for this
                     server. A maximum of five entries is allowed, and both
                     keys and values must be 255 characters or less.
        :param userdata: userdata file content (String)
        :param security_group_name_list: Sec. Groups ID list to be used by the instance
        :param network_id_list: (optional extension) an ordered list of nics to be
                      added to this server, with information about
                      connected networks, fixed ips, port etc.
                      Example: network_id_list=[{'net-id': network['id']}]
        :return: Instance data launched
        """

        nova_server_response = self.client.servers.create(name=instance_name, image=image_id, flavor=flavor_id,
                                                          key_name=keypair_name, meta=metadata,
                                                          userdata=userdata,
                                                          security_groups=security_group_name_list,
                                                          nics=network_id_list, min_count="1", max_count="1")

        self.logger.debug("Created server '%s': %s", instance_name, nova_server_response.id)
        return nova_server_response.to_dict()

    def get_server(self, instance_id):
        """
        Gets instance data from deployed server.
        :param instance_id: Deployed ServerID.
        :return:
        """
        nova_server_response = self.client.servers.get(instance_id)
        return nova_server_response.to_dict()

    def delete_server(self, instance_id):
        """
        Removes a server.
        :param instance_id: ServerID to be deleted.
        :return: None
        """
        self.client.servers.delete(instance_id)

    def list_servers(self, name_prefix=None):
        """
        Gets all the servers of the tenant
        :param name_prefix: Prefix to match server names
        :return: A list of :class:`Server`
        """
        server_list = self.client.servers.list()
        if name_prefix:
            server_list = [server for server in server_list if server.name.startswith(name_prefix)]

        return server_list

    def wait_for_task_status(self, server_id, expected_status):
        """
        Wait for a task status. This method will wait until the task has got the given status or 'ERROR' one.
        :param server_id: Deployed ServerID to be monitored
        :param expected_status: Expected status value
        :return: (Real task status at the end, Detailed reason to end waiting)
        """
        detail = "Server NOT {} after {} seconds".format(expected_status, MAX_WAIT_ITERATIONS * SLEEP_TIME)
        for i in range(MAX_WAIT_ITERATIONS):
            server_data = self.get_server(server_id)
            if server_data['status'] == expected_status:
                detail = "Server %s" % expected_status
                break
            elif server_data['status'] == 'ERROR':
                detail = server_data.get('fault', {'message': "Server NOT %s" % expected_status})['message']
                self.logger.error(detail)
                break

            self.logger.debug("Waiting (#%d) for status %s of instance %s (current is %s)...",
                              i+1, expected_status, server_id, server_data['status'])
            time.sleep(SLEEP_TIME)

        self.logger.debug("Status of instance %s is %s", server_id, server_data['status'])
        return server_data['status'], detail

    def allocate_ip(self, pool_name):
        """
        Create (allocate) a floating ip for a tenant
        :param pool_name: Name of the IP Pool
        :return: Allocated IP
        """
        allocated_ip_data = self.client.floating_ips.create(pool=pool_name)
        self.logger.debug("Allocated IP %s: %s", allocated_ip_data.ip, allocated_ip_data.id)
        return allocated_ip_data.to_dict()

    def deallocate_ip(self, ip_id):
        """
        Delete (deallocate) a  floating ip for a tenant
        :param ip_id: The floating ip address to delete.
        """
        self.client.floating_ips.delete(ip_id)
        self.logger.debug("Deallocated IP with id %s", ip_id)

    def list_allocated_ips(self):
        """
        Gets all the IPs currently allocated
        :return: IP list
        """
        return self.client.floating_ips.list()

    def add_floating_ip_to_instance(self, server_id, ip_address):
        """
        Adds a already allocated floating IP to VM
        :param server_id: Server ID where IP will be associated (String)
        :param ip_address: Allocated IP to be associated (String)
        :return: None
        """
        self.client.servers.add_floating_ip(server_id, ip_address, fixed_address=None)
