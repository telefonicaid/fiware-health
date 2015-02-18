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


from tests import fiware_region_base_tests
from commons.constants import WAIT_FOR_INSTANCE_ACTIVE, SLEEP_TIME, BASE_IMAGE_NAME


class FiwareRegionWithoutNetkorkTest(fiware_region_base_tests.FiwareRegionsBaseTests):

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

        flavor_id = self.nova_operations.get_any_flavor_id()
        self.assertIsNotNone(flavor_id, "Problems retrieving a flavor")

        image_id = self.nova_operations.find_image_id_by_name(image_name=BASE_IMAGE_NAME)
        self.assertIsNotNone(image_id, "Problems retrieving the image '{}'".format(BASE_IMAGE_NAME))

        if keypair_name is not None:
            keypair_value = self.nova_operations.create_keypair(keypair_name)
            self.test_world['keypair_names'].append(keypair_name)

        security_group_name_list = None
        if sec_group_name is not None:
            sec_group_id = self.nova_operations.create_security_group_and_rules(sec_group_name)
            self.test_world['sec_groups'].append(sec_group_id)
            security_group_name_list = [sec_group_name]

        server_data = self.nova_operations.launch_instance(instance_name=instance_name, flavor_id=flavor_id,
                                                           image_id=image_id,
                                                           metadata=metadata,
                                                           keypair_name=keypair_name,
                                                           security_group_name_list=security_group_name_list)
        self.test_world['servers'].append(server_data['id'])

        # Wait for status=ACTIVE
        status = self.nova_operations.wait_for_task_status(server_data['id'], 'ACTIVE')
        self.assertEqual(status, 'ACTIVE',
                         "Server launched is not ACTIVE after {seconds} seconds. Current Server status: {status}"
                         .format(seconds=WAIT_FOR_INSTANCE_ACTIVE*SLEEP_TIME, status=status))

    def test_deploy_instance_with_metadatas(self):
        """
        Test 17: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, Metadatas
        """
        self.__deploy_instance_helper__("testing_instance_03",
                                        metadata={"metadatatest01": "qatesting01"})

    def test_deploy_instance_with_keypair(self):
        """
        Test 18: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new Keypair
        """
        self.__deploy_instance_helper__("testing_instance_04",
                                        keypair_name="testing_keypair04")

    def test_deploy_instance_with_sec_group(self):
        """
        Test 19: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, new Sec. Group
        """
        self.__deploy_instance_helper__("testing_instance_05",
                                        sec_group_name="testing_sec_group_05")

    def test_deploy_instance_with_all_params(self):
        """
        Test 20: Check if it is possible to deploy a new Instance: Name, FlavorID, ImageID, Sec. Group, keypair, metadata
        """
        self.__deploy_instance_helper__("testing_instance_06",
                                        keypair_name="testing_keypair06",
                                        sec_group_name="testing_sec_group_06",
                                        metadata={"metadatatest01": "qatesting01"})
