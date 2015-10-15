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


from neutronclient.v2_0 import client
from neutronclient.common.exceptions import NeutronClientException
from commons.constants import *
import random


class FiwareNeutronOperations:

    def __init__(self, logger, region_name, tenant_id, **kwargs):
        """
        Initializes Neutron-Client.
        :param logger: Logger object
        :param region_name: FIWARE Region name
        :param tenant_id: Tenant identifier
        :param auth_session: Keystone auth session object
        :param auth_url: Keystone auth URL (needed if no session is given)
        :param auth_token: Keystone auth token (needed if no session is given)
        """

        self.logger = logger
        self.tenant_id = tenant_id
        self.client = client.Client(session=kwargs.get('auth_session'),
                                    auth_url=kwargs.get('auth_url'), token=kwargs.get('auth_token'),
                                    endpoint_type='publicURL', service_type="network",
                                    region_name=region_name, timeout=DEFAULT_REQUEST_TIMEOUT)

    def __build_body_create_network__(self, network_name, admin_state_up=True):
        """
        Builds the body to create a new network
        :param network_name: Network name
        :param admin_state_up: Admin state. By default, True
        :return: Body to be used in the request
        """
        body = {
            'network': {
                'name': network_name,
                'admin_state_up': admin_state_up
            }
        }
        return body

    def __build_body_create_subnetwork__(self, subnetwork_name, network_id, ip_version=4, enable_dhcp=True,
                                         dns_name_server=DEFAULT_DNS_SERVER, cidr=TEST_CIDR_DEFAULT):
        """
        Builds the body to create a new subnetwork
        :param subnetwork_name: Subnetwork name
        :param network_id: Parent network id
        :param ip_version: IP version. By default: 4
        :param enable_dhcp: If DHCP should be enables. By default: True
        :param dns_name_server: DNS name server to use in the network. By default: DEFAULT_DNS_SERVER
        :param cidr: CIDR to use for the subnetwork. By default: TEST_CIDR_DEFAULT
        :return: Body to be used in the request
        """
        body = {
            "subnet": {
                "name": subnetwork_name,
                "network_id": network_id,
                "cidr": cidr,
                "ip_version": ip_version,
                "tenant_id": self.tenant_id,
                "enable_dhcp": enable_dhcp,
                "dns_nameservers": [dns_name_server]
            }
        }
        return body

    def __build_body_create_router__(self, router_name, external_network_id=None):
        """
        Builds the body to create a new Router
        :param router_name: Router name
        :param external_network_id: External network ID to us as Gateway. By default: None
        :return: Body to be used in the request
        """
        body = {
            'router': {
                'external_gateway_info': {},
                'name': router_name
            }
        }
        if external_network_id is not None:
            body['router'].update({
                'external_gateway_info': {
                    'network_id': external_network_id
                }
            })
        return body

    def __build_body_add_interface__(self, subnetwork_id):
        """
        Build the body to add a new interface to Router
        :param subnetwork_id: Subnetwork ID
        :return: Body to be used when adding interfaces to router
        """
        body = {
            'subnet_id': subnetwork_id
        }
        return body

    def create_router(self, router_name, external_network_id=None):
        """
        Creates a new Router
        :param router_name: Name of the router
        :param external_network_id: Default Gateway to use in the router. By default: None
        :return: Python dict with created router data
        """
        create_router_body = self.__build_body_create_router__(router_name, external_network_id)
        neutron_network_response = self.client.create_router(create_router_body)
        self.logger.debug("Created router %s", neutron_network_response['router']['id'])
        return neutron_network_response['router']

    def add_interface_router(self, router_id, subnetwork_id):
        """
        Adds a new port to the router, linked to the given subnet
        :param router_id: Rotuer ID
        :param subnetwork_id: Subnetwork ID to be linked to the router
        :return: Port id (String)
        """
        add_interface_body = self.__build_body_add_interface__(subnetwork_id)
        response_body = self.client.add_interface_router(router=router_id, body=add_interface_body)
        self.logger.debug("Linked subnet '%s' to router %s", subnetwork_id, router_id)
        return response_body['port_id']

    def delete_interface_router(self, router_id, subnetwork_id):
        """
        Deletes the port from that subnet to the router
        :param router_id: Rotuer ID
        :param subnetwork_id: Subnetwork ID to remove the link to the router
        :return: None
        """
        add_interface_body = self.__build_body_add_interface__(subnetwork_id)
        self.client.remove_interface_router(router=router_id, body=add_interface_body)
        self.logger.debug("Deleted link from subnet '%s' to router %s", subnetwork_id, router_id)

    def list_ports(self):
        """
        Gets the list of ports.
        :return: A list of :class:`dict` with port data
        """
        return self.client.list_ports().get('ports')

    def show_port(self, port_id):
        """
        Gets a port data
        :param port_id: Port ID to retrieve its data
        :return: A port data :class:'dict'
        """
        return self.client.show_port(port_id).get('port')

    def delete_port(self, port_id):
        """
        Removes the given port by its ID
        :param port_id: Port id to be deleted
        :return:
        """
        self.client.delete_port(port_id)
        self.logger.debug("Deleted port %s", port_id)

    def delete_router(self, router_id):
        """
        Removes a created Router
        :param router_id: RouterID to be deleted
        :return: None
        """
        self.client.delete_router(router_id)
        self.logger.debug("Deleted router %s", router_id)

    def list_routers(self, name_prefix=None):
        """
        Gets the list of routers.
        :param name_prefix: Prefix to match router names
        :return: A list of :class:`dict` with router data
        """
        router_list = self.client.list_routers().get('routers')
        if name_prefix:
            router_list = [router for router in router_list if router['name'].startswith(name_prefix)]

        return router_list

    def create_network(self, network_name):
        """
        Creates a new network.
        :param network_name: Name of the network.
        :return: Python dict with created network data
        """
        body_network = self.__build_body_create_network__(network_name)
        neutron_network_response = self.client.create_network(body_network)
        self.logger.debug("Created network %s", neutron_network_response['network']['id'])
        return neutron_network_response['network']

    def create_subnet(self, network_dict, cidr=None):
        """
        Creates a subnet within a given network.
        :param network_dict: Python dict with created network data
        :param cidr: Optional CIDR to use for the subnet (otherwise, one is chosen from default range)
        :return: Python dict updated with created subnet data
        """
        subnetwork_name = "sub-{network_name}".format(network_name=network_dict['name'])
        body_subnetwork = self.__build_body_create_subnetwork__(subnetwork_name=subnetwork_name,
                                                                network_id=network_dict['id'])
        for i in range(1 if cidr else MAX_CIDR_SUBNET_ITERATIONS):
            body_subnetwork['subnet']['cidr'] = cidr or TEST_CIDR_PATTERN % random.choice(TEST_CIDR_RANGE)
            try:
                neutron_subnetwork_response = self.client.create_subnet(body_subnetwork)
                self.logger.debug("Created subnet %s", subnetwork_name)
                network_dict.update(neutron_subnetwork_response)
            except NeutronClientException as exc:
                self.logger.debug("Error #%d creating subnet %s: %s", i, subnetwork_name, exc)
            else:
                return network_dict
        raise exc

    def delete_network(self, network_id):
        """
        Removes a created network.
        :param network_id: NetworkID to be deleted
        :return: None
        """
        self.client.delete_network(network_id)
        self.logger.debug("Deleted network %s", network_id)

    def list_networks(self, name_prefix=None):
        """
        Gets the list of networks created by tenant.
        :param name_prefix: Prefix to match network names
        :return: A list of :class:`dict` with network data
        """
        network_list = self.find_networks(tenant_id=self.tenant_id)
        if name_prefix:
            network_list = [network for network in network_list if network['name'].startswith(name_prefix)]

        return network_list

    def find_networks(self, **kwargs):
        """
        Gets the list of networks matching attributes given in `kwargs`. To filter by "router:external" attribute,
        a keyword "router_external" must be supplied instead.
        :return: A list of :class:`dict` with network data
        """
        found = []
        search = [(key.replace('router_', 'router:'), value) for (key, value) in kwargs.items()]
        network_list = self.client.list_networks(retrieve_all=True).get('networks')
        for network in network_list:
            try:
                if all(network[attr] == value for (attr, value) in search):
                    found.append(network)
            except KeyError:
                continue

        return found
