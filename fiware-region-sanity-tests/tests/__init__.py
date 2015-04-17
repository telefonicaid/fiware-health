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


from commons.constants import PROPERTIES_LOGGER
from commons.fiware_cloud_test_case import FiwareTestCase
import logging


def setUpPackage():
    # Common logger for all suites
    logger_handler = logging.StreamHandler()
    logger_handler.setFormatter(logging.Formatter("%(levelname)s %(asctime)s %(message)s"))
    logger = logging.getLogger(PROPERTIES_LOGGER)
    logger.addHandler(logger_handler)
    logger.setLevel(logging.NOTSET)

    # Common settings
    FiwareTestCase.logger = logger
    FiwareTestCase.load_project_properties()
