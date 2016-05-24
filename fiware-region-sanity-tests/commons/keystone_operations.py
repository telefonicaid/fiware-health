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

from keystoneclient import client
from commons.constants import DEFAULT_REQUEST_TIMEOUT


class FiwareKeystoneOperations:

    def __init__(self, logger, region_name, tenant_id, user_id, **kwargs):
        """
        Initializes Keyston-client.
        :param logger: Logger object
        :param region_name: FIWARE Region name
        :param tenant_id: Tenant ID
        :param user_id: User ID
        """

        self.logger = logger
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.region_name = region_name
        self.client = client.Client(session=kwargs.get('auth_session'),
                                    auth_url=kwargs.get('auth_url'), auth_token=kwargs.get('auth_token'),
                                    endpoint_type='publicURL', endpoint_override=kwargs.get('auth_url'), service_type="identity",
                                    region_name=region_name,
                                    timeout=DEFAULT_REQUEST_TIMEOUT)

    def check_permited_role(self):
        """
        It checks the roles associated to the user in the project. In case it is admin, it
        exits the execution.
        :return: nothing
        """
        roles = self.client.roles.list(user=self.user_id, project=self.tenant_id)
        for role in roles:
            if "admin" in role.name:
                self.logger.debug("User with role admin cannot be used")
                raise Exception("User with role admin cannot be used")
