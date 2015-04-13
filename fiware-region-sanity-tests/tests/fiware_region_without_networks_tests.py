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

from novaclient.exceptions import OverLimit, Forbidden, ClientException
from tests import fiware_region_base_tests
from commons.constants import *
from datetime import datetime


class FiwareRegionWithoutNetworkTest(fiware_region_base_tests.FiwareRegionsBaseTests):

    with_networks = False

    def __deploy_instance_helper__(self, instance_name, keypair_name=None, sec_group_name=None, metadata=None):
        """
        HELPER. Creates an instance with the given data. If param is None, that one will not be passed to Nova.
            - Creates Keypair if keypair_name is not None
            - Creates Sec. Group if sec_group_name is not None
            - Adds metadata to server with teh given metadata dict.
        :param instance_name: Name of the new instance
        :param keypair_name: Name of the new keypair
        :param sec_group_name: Name of the new Sec. Group
        :param metadata: Python dict with metadata info {"key": "value"}
        :return: None
        """

        # skip if not all servers were deleted
        if self.test_world['servers']:
            self.skipTest("Not all the servers were deleted")

        flavor_id = self.nova_operations.get_any_flavor_id()
        self.assertIsNotNone(flavor_id, "Problems retrieving a flavor")

        image_id = self.nova_operations.find_image_id_by_name(image_name=BASE_IMAGE_NAME)
        self.assertIsNotNone(image_id, "Problems retrieving the image '{}'".format(BASE_IMAGE_NAME))

        # instance prerequisites
        try:
            if keypair_name:
                self.nova_operations.create_keypair(keypair_name)
                self.test_world['keypair_names'].append(keypair_name)
        except ClientException as e:
            self.logger.debug("Required keypair could not be created: %s", e)
            self.fail(e)

        try:
            security_group_name_list = None
            if sec_group_name:
                sec_group_id = self.nova_operations.create_security_group_and_rules(sec_group_name)
                self.test_world['sec_groups'].append(sec_group_id)
                security_group_name_list = [sec_group_name]
        except ClientException as e:
            self.logger.debug("Required security group could not be created: %s", e)
            self.fail(e)

        # create new instance
        try:
            server_data = self.nova_operations.launch_instance(instance_name=instance_name,
                                                               flavor_id=flavor_id,
                                                               image_id=image_id,
                                                               metadata=metadata,
                                                               keypair_name=keypair_name,
                                                               security_group_name_list=security_group_name_list)
        except Forbidden as e:
            self.logger.debug("Quota exceeded when launching a new instance")
            self.fail(e)
        except OverLimit as e:
            self.logger.debug("Not enough resources to launch new instance: %s", e)
            self.fail(e)
        else:
            self.test_world['servers'].append(server_data['id'])

        # Wait for status=ACTIVE
        status = self.nova_operations.wait_for_task_status(server_data['id'], 'ACTIVE')
        self.assertEqual(status, 'ACTIVE', "Server NOT ACTIVE after {seconds} seconds. Current status is {status}"
                         .format(seconds=MAX_WAIT_ITERATIONS*SLEEP_TIME, status=status))

    def test_deploy_instance_with_custom_metadata(self):
        """
        Test whether it is possible to deploy an instance with custom metadata
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_metadata_" + suffix
        instance_meta = {"test_item": "test_value"}
        self.__deploy_instance_helper__(instance_name=instance_name, metadata=instance_meta)

    def test_deploy_instance_with_keypair(self):
        """
        Test whether it is possible to deploy an instance with new keypair
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_keypair_" + suffix
        keypair_name = TEST_KEYPAIR_PREFIX + "_" + suffix
        self.__deploy_instance_helper__(instance_name=instance_name, keypair_name=keypair_name)

    def test_deploy_instance_with_sec_group(self):
        """
        Test whether it is possible to deploy an instance with new security group
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_name = TEST_SERVER_PREFIX + "_sec_group_" + suffix
        sec_group_name = TEST_SEC_GROUP_PREFIX + "_" + suffix
        self.__deploy_instance_helper__(instance_name=instance_name, sec_group_name=sec_group_name)

    def test_deploy_instance_with_all_params(self):
        """
        Test whether it is possible to deploy an instance with all params
        """
        suffix = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        instance_meta = {"test_item": "test_value"}
        instance_name = TEST_SERVER_PREFIX + "_all_params_" + suffix
        keypair_name = TEST_KEYPAIR_PREFIX + "_" + suffix
        sec_group_name = TEST_SEC_GROUP_PREFIX + "_" + suffix
        self.__deploy_instance_helper__(instance_name=instance_name, metadata=instance_meta,
                                        keypair_name=keypair_name, sec_group_name=sec_group_name)
