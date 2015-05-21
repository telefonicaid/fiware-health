#!/usr/bin/env python2.7
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


from xml.dom import minidom
from constants import PROPERTIES_FILE, PROPERTIES_CONFIG_KEY_TEST_CASES, PROPERTIES_CONFIG_OPT_TEST_CASES
import json
import sys
import re

ATTR_TESTS_TOTAL = "tests"
ATTR_TESTS_SKIP = "skip"
ATTR_TESTS_ERROR = "errors"
ATTR_TESTS_FAILURE = "failures"

CHILD_NODE_SKIP = "skipped"
CHILD_NODE_ERROR = "error"
CHILD_NODE_FAILURE = "failure"

TEST_STATUS_NOT_OK = "NOK"
TEST_STATUS_SKIP = "N/A"
TEST_STATUS_OK = "OK"

GLOBAL_STATUS_PARTIAL_OK = "POK"
GLOBAL_STATUS_NOT_OK = TEST_STATUS_NOT_OK
GLOBAL_STATUS_OK = TEST_STATUS_OK


class ResultAnalyzer(object):
    def __init__(self, file='test_results.xml'):
        self.file = file
        self.dict = {}

    def get_results(self):
        """
        Parse report file (xUnit test result report) to get total results per each Region.
        """
        doc = minidom.parse(self.file)
        testsuite = doc.getElementsByTagName("testsuite")[0]

        # Print a summary of the test results
        print "[Tests: {}, Errors: {}, Failures: {}, Skipped: {}]".format(
            testsuite.getAttribute(ATTR_TESTS_TOTAL),
            testsuite.getAttribute(ATTR_TESTS_ERROR),
            testsuite.getAttribute(ATTR_TESTS_FAILURE),
            testsuite.getAttribute(ATTR_TESTS_SKIP))

        # Count errors/failures/skips
        for testcase in doc.getElementsByTagName('testcase'):
            status = TEST_STATUS_OK
            child_node_list = testcase.childNodes
            if child_node_list is not None and len(child_node_list) != 0:
                if child_node_list[0].localName in [CHILD_NODE_FAILURE, CHILD_NODE_ERROR]:
                    status = TEST_STATUS_NOT_OK
                elif child_node_list[0].localName == CHILD_NODE_SKIP:
                    status = TEST_STATUS_SKIP

            testpackage = testcase.getAttribute('classname').split(".")[-2]
            testregion = testpackage.replace("test_", "")
            info_test = {"test_name": testcase.getAttribute('name'), "status": status}
            if testregion in self.dict:
                self.dict[testregion].append(info_test)
            else:
                self.dict.update({testregion: [info_test]})

    def print_results(self):
        """
        Print report through standard output
        """
        print "\n*********************************\n"
        print "REGION TEST SUMMARY REPORT: "
        for item in self.dict:
            print "\n >> {}".format(item)
            for result_value in self.dict[item]:
                print "  {status}\t {name}".format(name=result_value['test_name'], status=result_value['status'])

    def print_global_status(self):
        """
        This method will parse test results for each Region and will take into account whether all key and/or optional
        test cases are successful, according to the patterns defined in `settings.json`.
        :return:
        """
        with open(PROPERTIES_FILE) as config_file:
            try:
                conf = json.load(config_file)
            except Exception, e:
                print 'Error parsing config file: %s' % e

        # dict holding global status according either key or optional test cases
        global_status = {
            GLOBAL_STATUS_OK: {
                'caption': 'Regions satisfying all key test cases: %s' % conf[PROPERTIES_CONFIG_KEY_TEST_CASES],
                'empty_msg': 'NONE!!!!!!!',
                'region_list': []
            },
            GLOBAL_STATUS_PARTIAL_OK: {
                'caption': 'Regions only failing in optional test cases: %s' % conf[PROPERTIES_CONFIG_OPT_TEST_CASES],
                'empty_msg': 'N/A',
                'region_list': []
            }
        }

        # check status
        key_test_cases_patterns = [re.compile(item) for item in conf[PROPERTIES_CONFIG_KEY_TEST_CASES]]
        opt_test_cases_patterns = [re.compile(item) for item in conf[PROPERTIES_CONFIG_OPT_TEST_CASES]]
        for region, results in self.dict.iteritems():
            key_test_cases = [
                item for item in results
                if any(pattern.match(item['test_name']) for pattern in key_test_cases_patterns)
            ]
            non_opt_test_cases = [
                item for item in results
                if all(not pattern.match(item['test_name']) for pattern in opt_test_cases_patterns)
            ]

            if all(item['status'] == TEST_STATUS_OK for item in key_test_cases):
                global_status[GLOBAL_STATUS_OK]['region_list'].append(region)
            elif all(item['status'] == TEST_STATUS_OK for item in non_opt_test_cases):
                global_status[GLOBAL_STATUS_PARTIAL_OK]['region_list'].append(region)

        # print status
        print "\nREGION GLOBAL STATUS"
        for status in [GLOBAL_STATUS_OK, GLOBAL_STATUS_PARTIAL_OK]:
            region_list = global_status[status]['region_list']
            print "\n", global_status[status]['caption']
            print " >> %s" % ", ".join(region_list) if len(region_list) else " %s" % global_status[status]['empty_msg']


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print "Usage: python {} <xUnitResultFile.xml>".format(sys.argv[0])
        sys.exit(-1)

    checker = ResultAnalyzer(sys.argv[1])
    checker.get_results()
    checker.print_global_status()
    checker.print_results()
