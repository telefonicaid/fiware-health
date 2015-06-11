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

from tests.fiware_region_base_tests import FiwareRegionsBaseTests
from commons.constants import TEST_CONTAINER_PREFIX, TEST_TEXT_OBJECT_PREFIX, TEXT_EXTENSION, SWIFT_RESOURCES_PATH
from swiftclient.exceptions import ClientException as SwiftClientException
from datetime import datetime
import hashlib
import os

class FiwareRegionsObjectStorageTests(FiwareRegionsBaseTests):

    with_storage = True

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
        except SwiftClientException as e:
            self.assertRaises(e)
            self.logger.debug("%s container was successfully removed from the object storage" % containerName)

    def test_create_container_with_object_deleting_them(self):
        """
        Test if it can be possible create a new container into the object storage, upload a text file, download it and remove the
        object and the container.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S%m')
        containerName = TEST_CONTAINER_PREFIX + suffix
        textObjectName = TEST_TEXT_OBJECT_PREFIX + suffix

        response = self.swift_operations.create_container(containerName)
        self.assertIsNone(response)
        self.test_world['containers'].append(containerName)
        self.logger.debug("Created %s container was created" % containerName)

        ## Uploading the object

        response = self.swift_operations.create_text_object(containerName, SWIFT_RESOURCES_PATH
                                                            + TEST_TEXT_OBJECT_PREFIX + TEXT_EXTENSION,
                                                            textObjectName + TEXT_EXTENSION)
        origin = hashlib.md5(open(SWIFT_RESOURCES_PATH + TEST_TEXT_OBJECT_PREFIX + TEXT_EXTENSION, 'rb')
                          .read()).hexdigest()

        self.assertIsNone(response)
        self.logger.debug("Created %s object was created", textObjectName)

        ## Downloading the object
        response = self.swift_operations.get_text_object(containerName, textObjectName + TEXT_EXTENSION,
                                                         SWIFT_RESOURCES_PATH)
        self.assertTrue(response)

        remote = hashlib.md5(open(SWIFT_RESOURCES_PATH + textObjectName + TEXT_EXTENSION, 'rb')
                          .read()).hexdigest()

        ## Checking original file with remotefile
        self.assertEqual(origin, remote)

        #Cleaning the object
        os.remove(SWIFT_RESOURCES_PATH + textObjectName + TEXT_EXTENSION)

        response = self.swift_operations.delete_object(containerName, textObjectName + TEXT_EXTENSION)
        self.assertIsNone(response)

        response = self.swift_operations.delete_container(containerName)
        self.assertIsNone(response)
        self.test_world['containers'].remove(containerName)

        try:
            response = self.swift_operations.get_container(containerName)
        except SwiftClientException as e:
            self.assertRaises(e)
            self.logger.debug("%s container was successfully removed from the object storage" % containerName)
