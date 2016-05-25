#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2016 Telefónica Investigación y Desarrollo, S.A.U
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


"""Run tests (using nose) in selected region/s, according to command line arguments.

Usage:
  {prog} [nose_options] region|test_spec ...

Environment:
  OS_AUTH_URL                       The URL of OpenStack Identity Service for authentication
  OS_USERNAME                       The username for authentication
  OS_PASSWORD                       The password for authentication
  OS_USER_ID                        The user identifier for authentication
  OS_TENANT_ID                      The tenant identifier for authentication
  OS_TENANT_NAME                    The tenant name for authentication
  OS_USER_DOMAIN_NAME               (Only in Identity v3) The user domain name for authentication
  OS_PROJECT_DOMAIN_NAME            (Only in Identity v3) The project domain name for authentication
  SANITY_CHECKS_SETTINGS            (Optional) Path to settings file
  SANITY_CHECKS_LOGGING             (Optional) Path to logging configuration file
  TEST_PHONEHOME_ENDPOINT           (Optional) PhoneHome service endpoint

Files:
  resources/*                       Required support files
  etc/settings.json                 Default settings file
  etc/logging_sanitychecks.conf     Default logging configuration file

"""

import re
import sys
import os.path
import argparse
import json
import nose

parentdir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, parentdir)

from tests.fiware_region_with_networks_tests import FiwareRegionWithNetworkTest
from tests.fiware_region_without_networks_tests import FiwareRegionWithoutNetworkTest
from tests.fiware_region_object_storage_tests import FiwareRegionsObjectStorageTests
from commons.constants import DEFAULT_SETTINGS_FILE, DEFAULT_LOGGING_CONF, \
    PROPERTIES_CONFIG_REGION, PROPERTIES_CONFIG_REGION_SHARED_NET, PROPERTIES_CONFIG_SWIFT_ENABLED


class RegionTestsSelector(nose.selector.Selector):

    test_selections = None

    def wantMethod(self, method):
        region = method.im_class.__name__
        testname = '%s.%s' % (region, method.__name__)
        return super(RegionTestsSelector, self).wantMethod(method) and \
            any((selection == region or re.match(selection, testname)) for selection in self.test_selections)


class RegionTestsLoader(nose.loader.TestLoader):

    settings_file = None
    logging_conf = None
    test_regions = None
    home_dir = None

    def __init__(self, config=None, importer=None, workingDir=None, selector=None):
        super(RegionTestsLoader, self).__init__(config, importer, workingDir, RegionTestsSelector(config))

        with open(self.settings_file) as settings:
            try:
                self.conf = json.load(settings)
            except Exception as e:
                print "Error parsing settings file '{}': {}".format(self.settings_file, e)
                sys.exit(-1)

            region_conf = self.conf[PROPERTIES_CONFIG_REGION]
            region_list = [str(region) for region in region_conf.keys()]

            # Filter out regions to test, if given at command line
            self.test_regions = list(set(self.test_regions or region_list) & set(region_list))

            self.regions_with_network = [
                region for region in region_list if PROPERTIES_CONFIG_REGION_SHARED_NET in region_conf[region]
            ]
            self.regions_with_storage = [
                region for region in region_list if region_conf[region].get(PROPERTIES_CONFIG_SWIFT_ENABLED, False)
            ]

    def get_test_class(self, region):
        if region in self.regions_with_network:
            super_classes = [FiwareRegionWithNetworkTest]
        else:
            super_classes = [FiwareRegionWithoutNetworkTest]

        if region in self.regions_with_storage:
            super_classes.append(FiwareRegionsObjectStorageTests)

        return type(region, tuple(super_classes), dict(
            region_name=region,
            conf=self.conf,
            home_dir=self.home_dir,
            settings_file=self.settings_file,
            logging_conf=self.logging_conf))

    def loadTestsFromDir(self, path):
        test_classes = [self.get_test_class(region) for region in self.test_regions]
        for test_class in test_classes:
            yield self.loadTestsFromTestCase(test_class)


if __name__ == '__main__':
    # Get nose options and regions to test from command line
    parser = argparse.ArgumentParser()
    parser.add_argument('tests', metavar='test_spec', type=str, nargs='*')
    args, options = parser.parse_known_args()
    argv = [__file__] + options + ['.']
    RegionTestsSelector.test_selections = args.tests
    RegionTestsLoader.test_regions = [re.sub(r'^(\w+)\.\S+$', '\g<1>', test) for test in args.tests]

    # Configuration files
    default_settings_file = os.path.join(parentdir, DEFAULT_SETTINGS_FILE)
    default_logging_conf = os.path.join(parentdir, DEFAULT_LOGGING_CONF)
    RegionTestsLoader.settings_file = os.environ.get('SANITY_CHECKS_SETTINGS', default_settings_file)
    RegionTestsLoader.logging_conf = os.environ.get('SANITY_CHECKS_LOGGING', default_logging_conf)
    RegionTestsLoader.home_dir = parentdir

    # Run tests
    nose.main(argv=argv, testLoader=RegionTestsLoader)
