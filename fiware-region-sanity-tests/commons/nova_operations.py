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
from commons.constants import DEFAULT_REQUEST_TIMEOUT, SLEEP_TIME, WAIT_FOR_INSTANCE_ACTIVE
import time


class FiwareNovaOperations:

    def __init__(self, logger, region_name, **kwargs):
        """
        Initializes Nova-Client.
        :param logger: Logger object
        :param region_name: Fiware Region name
        :param auth_session: Keystone auth session object
        :param auth_url: Keystone auth URL (needed if no session is given)
        :param auth_token: Keystone auth token (needed if no session is given)
        """

        self.logger = logger
        self.client = client.Client(session=kwargs.get('auth_session'),
                                    auth_url=kwargs.get('auth_url'), auth_token=kwargs.get('auth_token'),
                                    endpoint_type='publicURL', service_type="compute",
                                    region_name=region_name, timeout=DEFAULT_REQUEST_TIMEOUT)

    def get_flavor_list(self):
        """
        Gets the list of flavors from the instantiated Nova client.
        :return: A list of Python dict with the retrieved flavor data
        """
        flavor_list = []

        nova_flavor_list = self.client.flavors.list()
        self.logger.debug("Flavor list: %s", nova_flavor_list)

        if nova_flavor_list is not None and len(nova_flavor_list) != 0:
            for flavor in nova_flavor_list:
                # Get full dict
                flavor = flavor.to_dict()
                flavor_list.append(flavor)

        return flavor_list

    def get_any_flavor_id(self):
        """
        Gets a flavor id from the available ones
        Gets the first flavor ID with name "small" or the last of all if no "small" are found
        :return: Flavor ID
        """
        flavor_list = self.get_flavor_list()

        flavor_id = None
        for flavor in flavor_list:
            if 'small' in flavor['name']:
                flavor_id = flavor['id']
                break
        flavor_id = flavor[-1] if flavor_id is None else flavor_id

        return flavor_id

    def get_image_list(self):
        """
        Gets the list of images from the instantiated Nova client.
        :return: List of Python dict with the retrieved image data
        """
        img_list = []

        nova_img_list = self.client.images.list()
        self.logger.debug("Image list: %s", nova_img_list)

        if nova_img_list is not None and len(nova_img_list) != 0:
            for image in nova_img_list:
                # Get full dict
                image = image.to_dict()
                img_list.append(image)

        return img_list

    def get_any_image_id(self):
        """
        Gets a image id from the available ones.
        Gets the first image with 'init' in its name
        :return: Image ID
        """
        # GET IMAGE
        image_list = self.get_image_list()

        # Get the first 'init' image
        image_id = None
        for image in image_list:
            if 'init' in image['name']:
                image_id = image['id']
                break
        return image_id

    def find_image_id_by_name(self, image_name):
        """
        Finds and returns the id of the first image by name
        :param image_name: Name of the image
        :return: First image that matches with the given name
        """
        nova_img_list = self.client.images.findall(name=image_name)
        if len(nova_img_list) != 0:
            return nova_img_list[0].to_dict()['id']
        else:
            return None

    def create_security_group_and_rules(self, name):
        """
        Creates a new Security Group and a default Rule (TCP/IP 22)
        :param name: Name of Sec. Group.
        :return: Security Group ID
        """
        sec_group_id = None

        nova_sec_group_created = self.client.security_groups.create(name, "Testing purpose")
        self.logger.debug("Created security group: %s", nova_sec_group_created)
        sec_group_id = nova_sec_group_created.to_dict()['id']

        nova_sec_group_rule = self.client.security_group_rules.create(sec_group_id, ip_protocol="TCP",
                                                                      from_port="22", to_port="22",
                                                                      cidr="0.0.0.0/0", group_id=None)
        self.logger.debug("Created security group rule (TCP 22 0.0.0.0/0): %s", nova_sec_group_rule)

        return sec_group_id

    def delete_security_group(self, id):
        """
        Removes the Sec. Group.
        :param id: Sec. Group to be deleted.
        :return: None
        """
        self.client.security_groups.delete(id)

    def create_keypair(self, name):
        """
        Creates new Keypair.
        :param name: Name of the Keypair
        :return: Private Key generated.
        """
        nova_keypair = self.client.keypairs.create(name)
        self.logger.debug("Created keypair: %s", nova_keypair)
        return nova_keypair.to_dict()['private_key']

    def delete_keypair(self, name):
        """
        Removes a Keypair.
        :param name: Name of the keypair to be deleted.
        :return: None
        """
        keypair = self.client.keypairs.find(name=name)
        self.client.keypairs.delete(keypair)

    def launch_instance(self, instance_name, image_id, flavor_id, keypair_name=None, metadata=None, userdata=None,
                        security_group_name_list=None, network_id_list=None):
        """
        Launches a new Service Instance.
        :param name: Something to name the server.
        :param image_id: The ImageID to boot with.
        :param flavor_id: The FlavorID to boot onto.
        :param keypair_name: (optional extension) name of previously created
                      keypair to inject into the instance.
        :param metadata:  A dict of arbitrary key/value metadata to store for this
                     server. A maximum of five entries is allowed, and both
                     keys and values must be 255 characters or less.
        :param userdata: user data to pass to be exposed by the metadata
                      server this can be a file type object as well or a
                      string.
        :param security_group_name_list: Sec. Groups ID list to be used by the instance
        :param network_id_list: (optional extension) an ordered list of nics to be
                      added to this server, with information about
                      connected networks, fixed ips, port etc.
                      Example: network_id_list=[{'net-id': network['id']}]
        :return: Instance data launched
        """
        nova_server_response = self.client.servers.create(name=instance_name, image=image_id, flavor=flavor_id,
                                                          key_name=keypair_name, meta=metadata, userdata=userdata,
                                                          security_groups=security_group_name_list,
                                                          nics=network_id_list, min_count="1", max_count="1")

        self.logger.debug("Created server: %s", nova_server_response.to_dict())
        return nova_server_response.to_dict()

    def get_server(self, instance_id):
        """
        Gets instance data from deployed server.
        :param instance_id: Deployed ServerID.
        :return:
        """
        nova_server_response = self.client.servers.get(instance_id)
        return nova_server_response.to_dict()

    def wait_for_task_status(self, server_id, status):
        """
        Wait for a task status. This method will wait until the task has got the given status or 'ERROR' one.
        :param server_id: Deployed ServerID to be monitored
        :param status: Status value
        :return: Real task status at the end
        """
        for i in range(WAIT_FOR_INSTANCE_ACTIVE):
            server_data = self.get_server(server_id)
            self.logger.debug("TIME {time}. Waiting for status '{expected_status}'. " +
                              "Instance: {server}. Current status: {status}".format(
                                  time=i, expected_status=status, server=server_id, status=server_data['status']))
            if server_data['status'] == status or server_data['status'] == 'ERROR':
                break
            time.sleep(SLEEP_TIME)  # Sleep SLEEP_TIME seconds.

        return server_data['status']

    def delete_instance(self, instance_id):
        """
        Removes a launched instance.
        :param instance_id: InstaceID to be deleted.
        :return: None
        """
        self.client.servers.delete(instance_id)

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
