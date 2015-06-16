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
from commons.constants import TEST_CONTAINER_PREFIX, TEST_TEXT_OBJECT_PREFIX, TEST_TEXT_FILE_EXTENSION, \
    SWIFT_RESOURCES_PATH, TEST_BIG_OBJECT_PREFIX, TEST_BIG_FILE_EXTENSION, BIG_FILE_URL_1, BIG_FILE_URL_2
from swiftclient.exceptions import ClientException as SwiftClientException
from datetime import datetime
import hashlib
import os


class FiwareRegionsObjectStorageTests(FiwareRegionsBaseTests):

    with_storage = True

    def test_create_container(self):
        """
        Test whether it is possible to create a new container into the object storage.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        containerName = TEST_CONTAINER_PREFIX + suffix

        response = self.swift_operations.create_container(containerName)

        self.assertIsNone(response, "Container could not be created")
        self.test_world['containers'].append(containerName)
        self.logger.debug("Created %s container was created", containerName)

        response = self.swift_operations.get_container(containerName)
        self.assertEquals('x-container-object-count' in response[0], True, "There is no container header in response")
        self.assertEquals(len(response[-1]), 0, "The container is not empty")  # The list of items should be 0.
        self.logger.debug("Getting %s container details from the object storage", containerName)

    def test_delete_container(self):
        """
        Test whether it is possible to delete a container.
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        containerName = TEST_CONTAINER_PREFIX + suffix

        response = self.swift_operations.create_container(containerName)
        self.assertIsNone(response, "Container could not be created")
        self.test_world['containers'].append(containerName)

        response = self.swift_operations.delete_container(containerName)
        self.assertIsNone(response, "Container could not be deleted")
        self.test_world['containers'].remove(containerName)

        try:
            self.swift_operations.get_container(containerName)
        except SwiftClientException as e:
            self.assertRaises(e)
            self.logger.debug("%s container was successfully removed from the object storage", containerName)

    def test_create_text_object_and_download_it(self):
        """
        Test whether it is possible to upload a text file and download it.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S%m')
        containerName = TEST_CONTAINER_PREFIX + suffix
        textObjectName = TEST_TEXT_OBJECT_PREFIX + suffix + TEST_TEXT_FILE_EXTENSION

        response = self.swift_operations.create_container(containerName)
        self.assertIsNone(response, "Container could not be created")
        self.test_world['containers'].append(containerName)
        self.logger.debug("Created %s container was created", containerName)

        ## Uploading the object
        try:
            response = self.swift_operations.create_object(containerName, SWIFT_RESOURCES_PATH
                                                                + TEST_TEXT_OBJECT_PREFIX + TEST_TEXT_FILE_EXTENSION,
                                                                textObjectName)
            origin = hashlib.md5(open(SWIFT_RESOURCES_PATH + TEST_TEXT_OBJECT_PREFIX + TEST_TEXT_FILE_EXTENSION, 'rb')
                              .read()).hexdigest()

            self.assertIsNotNone(response, "Object could not be created")
            self.test_world['swift_objects'].append(containerName + "/" + textObjectName)
            self.logger.debug("Created %s object was created", textObjectName)
        except Exception as ex:
            self.logger.error("Object %s has not been uploaded: ", textObjectName)
            self.fail(ex)

        ## Downloading the object
        try:
            response = self.swift_operations.get_object(containerName, textObjectName,
                                                             SWIFT_RESOURCES_PATH)
            self.assertTrue(response, "Object could not be downloaded")

            remote = hashlib.md5(open(SWIFT_RESOURCES_PATH + textObjectName, 'rb')
                              .read()).hexdigest()
        except Exception as ex:
            self.logger.error("Object %s has not been downloaded: ", textObjectName)
            self.fail(ex)

        ## Checking original file with remote file
        try:
            self.assertEqual(origin, remote, "The original file and the downloaded file are different")
        except AssertionError as e:
            self.logger.error("Object uploaded and object downloaded are different (%s)", textObjectName)
            self.fail(e)

        os.remove(SWIFT_RESOURCES_PATH + textObjectName)

    def test_delete_an_object_from_a_container(self):
        """
        Test whether it is possible to delete an object from a container.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S%m')
        containerName = TEST_CONTAINER_PREFIX + suffix
        textObjectName = TEST_TEXT_OBJECT_PREFIX + suffix + TEST_TEXT_FILE_EXTENSION

        response = self.swift_operations.create_container(containerName)
        self.assertIsNone(response, "Container could not be created")
        self.test_world['containers'].append(containerName)
        self.logger.debug("Created %s container was created", containerName)

        ## Uploading the object
        try:
            response = self.swift_operations.create_object(containerName, SWIFT_RESOURCES_PATH
                                                                + TEST_TEXT_OBJECT_PREFIX + TEST_TEXT_FILE_EXTENSION,
                                                                textObjectName)
            self.assertIsNotNone(response, "Object could not be created")
            self.test_world['swift_objects'].append(containerName + "/" + textObjectName)
            self.logger.debug("Created %s object was created", textObjectName)
        except Exception as ex:
            self.logger.error("Object %s has not been uploaded: ", textObjectName)
            self.fail(ex)

        #Cleaning the object
        try:
            response = self.swift_operations.delete_object(containerName, textObjectName)
            self.assertIsNone(response, "Container could not be deleted")
            self.test_world['swift_objects'].remove(containerName + "/" + textObjectName)
        except Exception as ex:
            self.logger.error("Object %s has not been deleted: ", textObjectName)
            self.fail(ex)

        try:
            self.swift_operations.get_object(containerName, textObjectName,
                                                             SWIFT_RESOURCES_PATH)
        except SwiftClientException as e:
            self.assertRaises(e)
            self.logger.debug("%s object was successfully removed from the object storage", textObjectName)

    def test_create_big_object_and_download_it(self):
        """
        Test whether it is possible to upload a big file and download it (More than 5Mb).
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S%m')
        containerName = TEST_CONTAINER_PREFIX + suffix
        big_object_name = TEST_BIG_OBJECT_PREFIX + suffix + TEST_BIG_FILE_EXTENSION

        response = self.swift_operations.create_container(containerName)
        self.assertIsNone(response, "Container could not be created")
        self.test_world['containers'].append(containerName)
        self.logger.debug("Created %s container was created", containerName)

        ## Creating a new big object
        import urllib2
        f = urllib2.urlopen(BIG_FILE_URL_1)
        data = f.read()
        with open(SWIFT_RESOURCES_PATH + TEST_BIG_OBJECT_PREFIX + TEST_BIG_FILE_EXTENSION, "wb") as code:
            code.write(data)

        ## Uploading the object
        try:
            response = self.swift_operations.create_object(containerName, SWIFT_RESOURCES_PATH
                                                                + TEST_BIG_OBJECT_PREFIX + TEST_BIG_FILE_EXTENSION,
                                                                big_object_name)
            origin = hashlib.md5(open(SWIFT_RESOURCES_PATH + TEST_BIG_OBJECT_PREFIX + TEST_BIG_FILE_EXTENSION, 'rb')
                              .read()).hexdigest()

            self.assertIsNotNone(response, "Object could not be created")
            self.test_world['swift_objects'].append(containerName + "/" + big_object_name)
            self.logger.debug("Created %s object was created", big_object_name)
        except Exception as ex:
            self.logger.error("Object %s has not been uploaded: ", big_object_name)
            self.fail(ex)

        ## Downloading the object
        try:
            response = self.swift_operations.get_object(containerName, big_object_name,
                                                             SWIFT_RESOURCES_PATH)
            self.assertTrue(response, "Object could not be downloaded")

            remote = hashlib.md5(open(SWIFT_RESOURCES_PATH + big_object_name, 'rb')
                              .read()).hexdigest()
        except Exception as ex:
            self.logger.error("Object %s has not been downloaded: ", big_object_name)
            self.fail(ex)

        ## Checking original file with remote file
        self.assertEqual(origin, remote, "The original file and the downloaded file are different")

        ##
        suffix2 = datetime.utcnow().strftime('%Y%m%d%H%M%S%m')
        f2 = urllib2.urlopen(BIG_FILE_URL_2)
        data = f2.read()
        with open(SWIFT_RESOURCES_PATH + TEST_BIG_OBJECT_PREFIX + suffix2 + TEST_BIG_FILE_EXTENSION, "wb") as code2:
            code2.write(data)

        ## Checking that two different files generates are different
        origin2 = hashlib.md5(open(SWIFT_RESOURCES_PATH + TEST_BIG_OBJECT_PREFIX + suffix2 + TEST_BIG_FILE_EXTENSION,
                                   'rb')
                              .read()).hexdigest()

        self.assertNotEqual(origin2, remote, "The second file and the downloaded file are the same, "
                                             "it cannot be possible")

        os.remove(SWIFT_RESOURCES_PATH + big_object_name)
        os.remove(SWIFT_RESOURCES_PATH + TEST_BIG_OBJECT_PREFIX + TEST_BIG_FILE_EXTENSION)
        os.remove(SWIFT_RESOURCES_PATH + TEST_BIG_OBJECT_PREFIX + suffix2 + TEST_BIG_FILE_EXTENSION)
