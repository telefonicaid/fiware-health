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

__author__ = 'gjp'


from swiftclient import client
from commons.constants import DEFAULT_REQUEST_TIMEOUT, MAX_RETRIES
import keystoneclient.v2_0.client as keystoneClient


class FiwareSwiftOperations:

    def __init__(self, logger, region_name, **kwargs):
        """
        Initializes Swift-Client.
        :param logger: Logger object
        :param region_name: Fiware Region name
        :param cred: Credentials to logging into keystone
        """

        self.logger = logger
        self.keystone_client = keystoneClient.Client(auth_url=kwargs.get('cred').auth_url,
                                                     username=kwargs.get('cred').username,
                                                     password=kwargs.get('cred').password,
                                                     tenant_id=kwargs.get('cred').tenant_name)

        object_store_url = self.keystone_client.service_catalog.url_for(service_type='object-store',
                                                       endpoint_type='publicURL', region_name=region_name)
        self.logger.info("Getting object_store_url from Keystone: %s" % object_store_url)

        self.client = client.Connection(
            preauthurl=object_store_url,
            preauthtoken=self.keystone_client.auth_token,
            retries=MAX_RETRIES,
            max_backoff=DEFAULT_REQUEST_TIMEOUT,
            insecure=True)

    def create_container(self, containerName):
        """
        Creates a new Container
        :param container_name: Name of the container
        :return: None if container was created and the error message if something failed.
        """
        response = self.client.put_container(containerName)
        return response

    def get_container(self, containerName):
        """
        Gets an specific Container
        :param container_name: Name of the container
        :return: Tuple with the request response about the container.
        """
        response = self.client.get_container(containerName)
        return response

    def delete_container(self, containerName):
        """
        Deletes a Container
        :param container_name: Name of the container
        :return: None if container was deleted and the error message if something failed.
        """
        response = self.client.delete_container(containerName)
        return response
