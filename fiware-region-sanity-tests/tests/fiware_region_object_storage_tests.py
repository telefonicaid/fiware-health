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


from tests.fiware_region_base_tests import FiwareRegionsBaseTests
from commons.constants import TEST_CONTAINER_PREFIX, TEST_TEXT_OBJECT_BASENAME, TEST_TEXT_FILE_EXTENSION, \
    SWIFT_RESOURCES_PATH, SWIFT_TMP_RESOURCES_PATH, TEST_BIG_OBJECT_BASENAME, TEST_BIG_FILE_EXTENSION, \
    PROPERTIES_CONFIG_SWIFT,\
    PROPERTIES_CONFIG_SWIFT_BIG_FILE_1, PROPERTIES_CONFIG_SWIFT_BIG_FILE_2, PROPERTIES_CONFIG_TEST,\
    TEST_BIG_OBJECT_REMOTE
from swiftclient.exceptions import ClientException as SwiftClientException
from datetime import datetime
import hashlib
import urllib2
import os


class FiwareRegionsObjectStorageTests(FiwareRegionsBaseTests):

    with_storage = True

    def test_create_container(self):
        """
        Test whether it is possible to create a new container into the object storage.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        container_name = TEST_CONTAINER_PREFIX + suffix

        response = self.swift_operations.create_container(container_name)

        self.assertIsNone(response, "Container could not be created")
        self.test_world['containers'].append(container_name)
        self.logger.debug("Created %s container was created", container_name)

        response = self.swift_operations.get_container(container_name)
        self.assertEquals('x-container-object-count' in response[0], True, "There is no container header in response")
        self.assertEquals(len(response[-1]), 0, "The container is not empty")  # The list of items should be 0.
        self.logger.debug("Getting %s container details from the object storage", container_name)

    def test_delete_container(self):
        """
        Test whether it is possible to delete a container.
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        container_name = TEST_CONTAINER_PREFIX + suffix

        response = self.swift_operations.create_container(container_name)
        self.assertIsNone(response, "Container could not be created")
        self.test_world['containers'].append(container_name)

        response = self.swift_operations.delete_container(container_name)
        self.assertIsNone(response, "Container could not be deleted")
        self.test_world['containers'].remove(container_name)

        try:
            self.swift_operations.get_container(container_name)
        except SwiftClientException as e:
            self.assertRaises(e)
            self.logger.debug("%s container was successfully removed from the object storage", container_name)

    def test_create_text_object_and_download_it_from_container(self):
        """
        Test whether it is possible to upload a text file and download it.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S%m')
        container_name = TEST_CONTAINER_PREFIX + suffix
        text_object_name = self.region_name + TEST_TEXT_OBJECT_BASENAME + suffix + TEST_TEXT_FILE_EXTENSION

        response = self.swift_operations.create_container(container_name)
        self.assertIsNone(response, "Container could not be created")
        self.test_world['containers'].append(container_name)
        self.logger.debug("Created %s container was created", container_name)

        # Uploading the object
        response = self.swift_operations.create_object(container_name, SWIFT_RESOURCES_PATH +
                                                       TEST_TEXT_OBJECT_BASENAME + TEST_TEXT_FILE_EXTENSION,
                                                       text_object_name)
        origin = hashlib.md5(open(SWIFT_RESOURCES_PATH + TEST_TEXT_OBJECT_BASENAME +
                                  TEST_TEXT_FILE_EXTENSION, 'rb').read()).hexdigest()

        self.assertIsNotNone(response, "Object could not be created")
        self.test_world['swift_objects'].append(container_name + "/" + text_object_name)
        self.logger.debug("Created %s object was created", text_object_name)

        # Downloading the object
        response = self.swift_operations.get_object(container_name, text_object_name, SWIFT_TMP_RESOURCES_PATH)
        self.assertTrue(response, "Object could not be downloaded")
        self.test_world['local_objects'].append(text_object_name)

        remote = hashlib.md5(open(SWIFT_TMP_RESOURCES_PATH + text_object_name, 'rb').read()).hexdigest()

        # Checking original file with remote file
        try:
            self.assertEqual(origin, remote, "The original file and the downloaded file are different")
        except AssertionError as e:
            self.logger.error("Object uploaded and object downloaded are different (%s)", text_object_name)
            self.fail(e)

    def test_delete_an_object_from_a_container(self):
        """
        Test whether it is possible to delete an object from a container.
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S%m')
        container_name = TEST_CONTAINER_PREFIX + suffix
        text_object_name = self.region_name + TEST_TEXT_OBJECT_BASENAME + suffix + TEST_TEXT_FILE_EXTENSION

        response = self.swift_operations.create_container(container_name)
        self.assertIsNone(response, "Container could not be created")
        self.test_world['containers'].append(container_name)
        self.logger.debug("Created %s container was created", container_name)

        # Uploading the object
        response = self.swift_operations.create_object(container_name, SWIFT_RESOURCES_PATH +
                                                       TEST_TEXT_OBJECT_BASENAME + TEST_TEXT_FILE_EXTENSION,
                                                       text_object_name)
        self.assertIsNotNone(response, "Object could not be created")
        self.test_world['swift_objects'].append(container_name + "/" + text_object_name)
        self.logger.debug("Created %s object was created", text_object_name)

        # Cleaning the object
        response = self.swift_operations.delete_object(container_name, text_object_name)
        self.assertIsNone(response, "Container could not be deleted")
        self.test_world['swift_objects'].remove(container_name + "/" + text_object_name)

        try:
            self.swift_operations.get_object(container_name, text_object_name, SWIFT_TMP_RESOURCES_PATH)
        except SwiftClientException as e:
            self.assertRaises(e)
            self.logger.debug("%s object was successfully removed from the object storage", text_object_name)

    def test_create_big_object_and_download_it_from_container(self):
        """
        Test whether it is possible to upload a big file and download it (More than 5Mb).
        """

        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S%m')
        container_name = TEST_CONTAINER_PREFIX + suffix
        big_object_name = self.region_name + TEST_BIG_OBJECT_BASENAME + TEST_BIG_FILE_EXTENSION
        remote_big_object_name = self.region_name + TEST_BIG_OBJECT_REMOTE + TEST_BIG_OBJECT_BASENAME + \
            suffix + TEST_BIG_FILE_EXTENSION

        response = self.swift_operations.create_container(container_name)
        self.assertIsNone(response, "Container could not be created")
        self.test_world['containers'].append(container_name)
        self.logger.debug("Created %s container was created", container_name)

        # Creating a new big object if do not exits
        if not os.path.isfile(SWIFT_TMP_RESOURCES_PATH + big_object_name):
            big_file_url_1 = \
                self.conf[PROPERTIES_CONFIG_TEST][PROPERTIES_CONFIG_SWIFT][PROPERTIES_CONFIG_SWIFT_BIG_FILE_1]
            f = urllib2.urlopen(big_file_url_1)
            data = f.read()

            try:
                with open(SWIFT_TMP_RESOURCES_PATH + big_object_name, "wb") as code:
                        code.write(data)
            except IOError:
                self.logger.error("Error while writing %s file", SWIFT_TMP_RESOURCES_PATH + big_object_name)

        # Uploading the object
        response = self.swift_operations.create_object(container_name, SWIFT_TMP_RESOURCES_PATH + big_object_name,
                                                       remote_big_object_name)
        origin_hash = hashlib.md5(open(SWIFT_TMP_RESOURCES_PATH + big_object_name, 'rb').read()).hexdigest()

        self.assertIsNotNone(response, "Object could not be created")
        self.test_world['swift_objects'].append(container_name + "/" + remote_big_object_name)
        self.logger.debug("Created %s object with name %s", big_object_name, remote_big_object_name)

        # Downloading the object
        response = self.swift_operations.get_object(container_name, remote_big_object_name, SWIFT_TMP_RESOURCES_PATH)
        self.assertTrue(response, "Object could not be downloaded")
        self.test_world['local_objects'].append(remote_big_object_name)

        remote_hash = hashlib.md5(open(SWIFT_TMP_RESOURCES_PATH + remote_big_object_name, 'rb').read()).hexdigest()

        # Checking original file with remote file
        self.assertEqual(origin_hash, remote_hash, "The original file and the downloaded file are different")

        # Downloading a second big file to check that is different
        suffix2 = "second_file"
        if not os.path.isfile(SWIFT_TMP_RESOURCES_PATH + self.region_name + TEST_BIG_OBJECT_BASENAME + suffix2 +
                              TEST_BIG_FILE_EXTENSION):
            big_file_url_2 = \
                self.conf[PROPERTIES_CONFIG_TEST][PROPERTIES_CONFIG_SWIFT][PROPERTIES_CONFIG_SWIFT_BIG_FILE_2]
            f2 = urllib2.urlopen(big_file_url_2)
            data = f2.read()
            try:
                with open(SWIFT_TMP_RESOURCES_PATH + self.region_name + TEST_BIG_OBJECT_BASENAME + suffix2 +
                          TEST_BIG_FILE_EXTENSION, "wb") as code2:
                    code2.write(data)
            except IOError:
                self.logger.error("Error while writing %s file", SWIFT_TMP_RESOURCES_PATH + self.region_name +
                                  TEST_BIG_OBJECT_BASENAME + suffix2 + TEST_BIG_FILE_EXTENSION)

        # Checking that two different files generates are different
        origin2 = hashlib.md5(open(SWIFT_TMP_RESOURCES_PATH + self.region_name + TEST_BIG_OBJECT_BASENAME + suffix2 +
                                   TEST_BIG_FILE_EXTENSION, 'rb').read()).hexdigest()

        self.assertNotEqual(origin2, remote_hash, "The second file and the downloaded file are the same,"
                                                  " it cannot be possible")
