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


from swiftclient import client
from commons.constants import DEFAULT_REQUEST_TIMEOUT, OBJECT_STORE_MAX_RETRIES, SERVICE_SWIFT_NAME,\
    ENDPOINT_TYPE_PUBLIC_URL, PROPERTIES_CONFIG_CRED_KEYSTONE_URL,\
    PROPERTIES_CONFIG_CRED_USERNAME, PROPERTIES_CONFIG_CRED_PASSWORD, PROPERTIES_CONFIG_CRED_TENANT_ID,\
    PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME, PROPERTIES_CONFIG_CRED_PROJECT_DOMAIN_NAME

import keystoneclient.v2_0.client as keystoneClient
import keystoneclient.v3.client as keystoneclientv3


class FiwareSwiftOperations:

    # TODO import keystoneclient dynamically from api version.
    # TODO Session is not taken from kwargs because swiftclient does not support it yet. It is needed auth credentials

    def __init__(self, logger, region_name, auth_api, **kwargs):
        """
        Initializes Swift-Client.
        :param logger: Logger object
        :param region_name: FIWARE Region name
        :param auth_api: Authentication API version
        :param kwargs: Keystone credentials
        """
        self.region_name = region_name

        self.logger = logger
        if auth_api == 'v2.0':
            self.keystone_client = keystoneClient.Client(
                auth_url=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_KEYSTONE_URL],
                username=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_USERNAME],
                password=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_PASSWORD],
                tenant_id=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_TENANT_ID])
        elif auth_api == 'v3':
            self.keystone_client = keystoneclientv3.Client(
                auth_url=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_KEYSTONE_URL],
                username=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_USERNAME],
                password=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_PASSWORD],
                user_domain_name=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_USER_DOMAIN_NAME],
                project_domain_name=kwargs.get('auth_cred')[PROPERTIES_CONFIG_CRED_PROJECT_DOMAIN_NAME])

        object_store_url = self.keystone_client.service_catalog.url_for(service_type=SERVICE_SWIFT_NAME,
                                                                        endpoint_type=ENDPOINT_TYPE_PUBLIC_URL,
                                                                        region_name=self.region_name)

        self.logger.info("Getting object_store_url from Keystone: %s", object_store_url)

        self.client = client.Connection(
            preauthurl=object_store_url,
            preauthtoken=self.keystone_client.auth_token,
            retries=OBJECT_STORE_MAX_RETRIES,
            max_backoff=DEFAULT_REQUEST_TIMEOUT,
            insecure=True)

    def list_containers(self, name_prefix=None):
        """
        Gets all the containers
        :param name_prefix: Prefix to match container names
        :return: A list of container names
        """
        container_list = self.client.get_account()[1]

        if name_prefix:
            container_list = [container for container in container_list if container["name"].startswith(name_prefix)]

        return container_list

    def create_container(self, container_name):
        """
        Creates a new Container
        :param container_name: Name of the container
        :return: None if container was created and the error message if something failed.
        """
        response = self.client.put_container(container_name)
        return response

    def create_object(self, container_name, local_file, object_name):
        """
        Creates a new object into a container
        :param container_name: Name of the container
        :param local_file: Name of the local file
        :param object_name: Name of the object
        :return: None if object was created and the error message if something failed.
        """
        with open(local_file, 'r') as test_file:
            response = self.client.put_object(container_name, object_name, contents=test_file.read())
            return response

    def get_object(self, container_name, object_name, download_path):
        """
        Downloads a object from a container
        :param container_name: Name of the container
        :param object_name: Name of the object
        :param download_path: Path to download folder
        :return: returns True when the object was downloaded.
        """
        obj = self.client.get_object(container_name, object_name)
        with open(download_path + object_name, 'w') as test_file:
            test_file.write(obj[1])
        return True

    def delete_object(self, container_name, object_name):
        """
        Deletes an Object
        :param container_name: Name of the container
        :param object_name: Name of the object
        :return: None if object was deleted and the error message if something failed.
        """
        response = self.client.delete_object(container_name, object_name)
        return response

    def get_container(self, container_name):
        """
        Gets an specific Container
        :param container_name: Name of the container
        :return: Tuple with the request response about the container.
        """
        response = self.client.get_container(container_name)
        return response

    def delete_container(self, container_name):
        """
        Deletes a Container
        :param container_name: Name of the container
        :return: None if container was deleted and the error message if something failed.
        """
        response = self.client.delete_container(container_name)
        return response
