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

from tests import fiware_region_base_tests
from commons.constants import TEST_CONTAINER_PREFIX
from swiftclient.exceptions import ClientException
from datetime import datetime


class FiwareRegionsObjectStorageTests(fiware_region_base_tests.FiwareRegionsBaseTests):

    def test_create_get_and_delete_container(self):
        """
        Test if it can be possible create a new container into the object storage, list it and delete the container.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        containerName = TEST_CONTAINER_PREFIX + suffix

        response = self.swift_operations.create_container(containerName)
        self.assertIsNone(response)
        self.test_world['containers'].append(containerName)
        self.logger.debug("Created %s container was created" % containerName)

        response = self.swift_operations.get_container(containerName)
        self.assertEquals('x-container-object-count' in response[0], True)
        self.assertEquals(len(response[-1]), 0)  # The list of items should be 0.
        self.logger.debug("Getting %s container details from the object storage" % containerName)

        response = self.swift_operations.delete_container(containerName)
        self.assertIsNone(response)
        self.test_world['containers'].remove(containerName)

        try:
            response = self.swift_operations.get_container(containerName)
        except ClientException as e:
            self.assertRaises(e)
            self.logger.debug("%s container was successfully removed from the object storage" % containerName)

    def test_create_container(self):
        """
        Test if it can be possible create a new container into the object storage.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S%m')
        containerName = TEST_CONTAINER_PREFIX + suffix

        response = self.swift_operations.create_container(containerName)
        self.assertIsNone(response)
        self.test_world['containers'].append(containerName)
        self.logger.debug("Created %s container was created" % containerName)
