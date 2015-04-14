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
from constants import PROPERTIES_FILE, PROPERTIES_CONFIG_KEYTESTCASES
import json
import sys


class ResultAnalyzer(object):

    def __init__(self, file='test_results.xml'):
        self.file = file
        self.test = 0
        self.failures = 0
        self.dict = {}

    def get_results(self):
        """
        Parse report file (xUnit test result report) to get total results per each Region.
        """

        doc = minidom.parse(self.file)

        testsuite = doc.getElementsByTagName("testsuite")[0]

        # Print the total tests and failures
        print "{} [Tests: {}, Errors: {}, Failures: {}, Skipped: {}]".format(
            testsuite.getAttribute("name"), testsuite.getAttribute("tests"), testsuite.getAttribute("errors"),
            testsuite.getAttribute("failures"), testsuite.getAttribute("skip"))

        # Total Tests
        self.test += int(testsuite.getAttribute("tests"))

        # Total Fail and Error Tests
        self.failures += int(testsuite.getAttribute("failures")) + int(testsuite.getAttribute("errors"))

        for testcase in doc.getElementsByTagName('testcase'):
            # Count errors/failures
            status = "OK"
            child_node_list = testcase.childNodes
            if child_node_list is not None and len(child_node_list) != 0:
                if child_node_list[0].localName == "failure" or child_node_list[0].localName == "error":
                    status = "NOK"

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

    def get_regions_with_key_test_cases_passed(self):
        """
        This method will parse all test results for each Region and will take in account only test cases defined in the
        settings.json file to consider is Regions is OK or NOT.
        :return:
        """

        region_ok_list = []

        with open(PROPERTIES_FILE) as config_file:
            try:
                conf = json.load(config_file)
            except Exception, e:
                print 'Error parsing config file: %s' % e

        key_test_cases_list = conf[PROPERTIES_CONFIG_KEYTESTCASES]
        for item in self.dict:
            passed = True
            for result_value in self.dict[item]:
                passed = True
                for key_test_case in key_test_cases_list:
                    if key_test_case in result_value['test_name']:
                        if result_value['status'] != 'OK':
                            passed = False
                            break
                if not passed:
                    break
            if passed:
                region_ok_list.append(item)

        print "\nREGION GLOBAL STATUS\n"
        print "Key Test Cases list:", str(key_test_cases_list)
        print "Region list with that test cases as PASSED status:"
        if len(region_ok_list) == 0:
            print "NONE!!!!!!!"
        else:
            for region in region_ok_list:
                print " >> {}".format(region)

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print " Usage: python {} <xUnitResultFile.xml>".format(sys.argv[0])
        sys.exit(-1)

    checker = ResultAnalyzer(str(sys.argv[1]))
    checker.get_results()
    checker.get_regions_with_key_test_cases_passed()
    checker.print_results()
