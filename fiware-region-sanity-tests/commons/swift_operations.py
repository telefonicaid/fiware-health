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
from commons.constants import DEFAULT_REQUEST_TIMEOUT, OBJECT_STORE_MAX_RETRIES, PROPERTIES_CONFIG_CRED_KEYSTONE_URL, \
    PROPERTIES_CONFIG_CRED_USER, PROPERTIES_CONFIG_CRED_PASS, PROPERTIES_CONFIG_CRED_TENANT_ID, SERVICE_SWIFT_NAME, \
    ENDPOINT_TYPE_PUBLIC_URL, PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME
import keystoneclient.v2_0.client as keystoneClient
import keystoneclient.v3.client as keystoneclientv3


class FiwareSwiftOperations:

    def __init__(self, logger, region_name, auth_api, **kwargs):
        """
        Initializes Swift-Client.
        :param logger: Logger object
        :param region_name: Fiware Region name
        :param cred: Credentials to logging into keystone
        """

        self.logger = logger
        if auth_api == 'v2.0':
            self.keystone_client = keystoneClient.Client(
                auth_url=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_KEYSTONE_URL],
                username=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_USER],
                password=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_PASS],
                tenant_id=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_TENANT_ID])
        elif auth_api == 'v3':
            self.keystone_client = keystoneclientv3.Client(
                auth_url=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_KEYSTONE_URL],
                username=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_USER],
                password=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_PASS],
                user_domain_name=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME])

        object_store_url = self.keystone_client.service_catalog.url_for(service_type=SERVICE_SWIFT_NAME,
                                                       endpoint_type=ENDPOINT_TYPE_PUBLIC_URL, region_name=region_name)
        self.logger.info("Getting object_store_url from Keystone: %s" % object_store_url)

        self.client = client.Connection(
            preauthurl=object_store_url,
            preauthtoken=self.keystone_client.auth_token,
            retries=OBJECT_STORE_MAX_RETRIES,
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
