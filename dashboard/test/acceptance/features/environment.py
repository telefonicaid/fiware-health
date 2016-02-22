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

import behave
from qautils.logger.logger_utils import get_logger
import qautils.configuration.configuration_utils as configuration_manager

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


__author__ = "Telefonica I+D"
__copyright__ = "Copyright 2015"
__license__ = " Apache License, Version 2.0"

__logger__ = get_logger("behave_environment")

# Use regular expressions for step param definition (Behave).
behave.use_step_matcher("re")


def before_all(context):
    """
    HOOK: To be executed before all.
        - Load project properties
    """

    __logger__.info("Setting UP execution")

    # Load project properties.
    # The loaded properties will be available in 'configuration_manager.config'
    __logger__.info("Loading project properties")
    configuration_manager.set_up_project()
    config = configuration_manager.config

    context.dashboard_url = config['dashboard']['protocol'] + '://' + \
        config['dashboard']['host'] + ':' + \
        config['dashboard']['port'] + \
        config['dashboard']['web_context']

    if config['dashboard']['selenium'] == 'yes':
        context.selenium = True
        context.driver = webdriver.Firefox()
    else:
        context.selenium = False


def before_feature(context, feature):
    """
    HOOK: To be executed before each Feature.
    """

    __logger__.info("Starting execution of feature")
    __logger__.info("##############################")
    __logger__.info("##############################")


def after_feature(context, feature):
    """
    HOOK: To be executed after each Feature.
        - Remove generated key files.
    """

    __logger__.info("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    __logger__.info("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    __logger__.info("Tearing down execution of feature")


def after_all(context):
    """
    HOOK: To be executed after all.
    """

    __logger__.info("Tearing down execution")
    if context.selenium:
        context.driver.close()
