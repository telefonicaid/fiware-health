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


from neutronclient.v2_0 import client
from commons.constants import DEFAULT_REQUEST_TIMEOUT


class FiwareNeutronOperations:

    def __init__(self, username, password, tenant_id, keystone_url, region_name):
        """
        Inits Neutron Rest Client. Url will be loaded from Keystone Service Catalog (publicURL, network service)
        :param username: Fiware username
        :param password: Fiware password
        :param tenant_id: Fiware Tenant ID
        :param keystone_url: Keystore URL
        :param region_name: Fiware Region name
        :return: None
        """
        self.tenant_id = tenant_id
        self.client = client.Client(username=username, password=password, tenant_id=tenant_id, auth_url=keystone_url,
                                    endpoint_type='publicURL', service_type="network", region_name=region_name,
                                    timeout=DEFAULT_REQUEST_TIMEOUT)

    def __build_body_create_network__(self, network_name, admin_state_up=True):
        """
        Builds the body to create a new network
        :param network_name: Network name
        :param admin_state_up: Admin state. By default, True
        :return: Body to be used in the request
        """
        body = {'network': {'name': network_name, 'admin_state_up': admin_state_up}}
        return body

    def __build_body_create_subnetwork__(self, subnetwork_name, network_id, cidr, ip_version, enable_dhcp=True):
        """
        Builds the body to create a new subnetwork
        :param subnetwork_name: Subnetwork name
        :param network_id: Parent network id
        :param cidr: CIDR
        :param ip_version: IP version. By default: 4
        :param enable_dhcp: If DHCP should be enables. By default: True
        :return: Body to be used in the request
        """
        body = {"subnet": {"name": subnetwork_name, "network_id": network_id, "cidr": cidr, "ip_version": ip_version,
                           "tenant_id": self.tenant_id, "enable_dhcp": enable_dhcp}}
        return body

    def __build_body_create_router__(self, router_name, external_network_id=None):
        """
        Builds the body to create a new Router
        :param router_name: Router name
        :param external_network_id: External network ID to us as Gateway. By default: None
        :return: Body to be used in the request
        """
        body = {'router': {'external_gateway_info': {}, 'name': router_name}}
        if external_network_id is not None:
            body.update({'router': {'external_gateway_info': {'network_id': external_network_id}}})
        return body

    def get_network_list(self):
        """
        Gets the list of created networks.
        :return: List of networks
        """
        return self.client.list_networks(retrieve_all=True)

    def get_network_external_list(self):
        """
        Gets the list of created networks with attribute router:external = True
        :return: List of external networks
        """
        network_list = self.get_network_list()
        external_network_list = list()
        for network in network_list['networks']:
            if network['router:external'] is True:
                external_network_list.append(network)
        return external_network_list

    def create_router(self, router_name, external_network_id=None):
        """
        Creates a new Router
        :param router_name: Name of the router
        :param external_network_id: Default Gateway to use in the router. By default: None
        :return: Python dict with created router data
        """
        create_router_body = self.__build_body_create_router__(router_name, external_network_id)
        neutron_network_response = self.client.create_router(create_router_body)
        print "Created router:", neutron_network_response

        return neutron_network_response['router']

    def delete_router(self, router_id):
        """
        Removes a created Router
        :param router_id: RouterID to be deleted
        :return: None
        """
        self.client.delete_router(router_id)

    def create_network_and_subnet(self, network_name, cidr="192.168.100.0/24"):
        """
        Creates a new network with one subnet.
        :param network_name: Name of the network. (Subnet will be called sub-{network_name})
        :param cidr: CIDR to be used by subnet
        :return: Python dict with all created network data
        """
        # Create network
        body_network = self.__build_body_create_network__(network_name)
        neutron_network_response = self.client.create_network(body_network)

        # Create subnetwork
        subnetwork_name = "sub-{network_name}".format(network_name=network_name)
        body_subnetwork = self.__build_body_create_subnetwork__(subnetwork_name=subnetwork_name,
                                                                network_id=neutron_network_response['network']['id'],
                                                                cidr=cidr,
                                                                ip_version="4")
        neutron_subnetwork_response = self.client.create_subnet(body_subnetwork)
        neutron_network_response['network'].update(neutron_subnetwork_response)

        print "Created network and sub-network:", neutron_network_response['network']
        return neutron_network_response['network']

    def delete_network(self, network_id):
        """
        Removes a created network.
        :param network_id: NetworkID to be deleted
        :return: None
        """
        self.client.delete_network(network_id)
