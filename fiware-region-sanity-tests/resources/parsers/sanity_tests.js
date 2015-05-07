/*
 * Copyright 2015 Telefónica I+D
 * All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */


/**
 * Module that defines a parser for the results of FiHealth Sanity Checks.
 *
 * Context attributes to be calculated:
 *
 * - sanity_status = global status of the region
 * - sanity_{test} = status of each individual {test}
 *
 * @module sanity_tests
 * @see https://github.com/telefonicaid/fiware-health/blob/master/fiware-region-sanity-tests
 */


'use strict';
/* jshint -W101, unused: false */


/**
 * Parser for FiHealth Sanity Checks.
 * @augments base
 */
var parser = Object.create(require('./common/base').parser);


/**
 * Parses the request to extract raw data.
 *
 * @function parseRequest
 * @memberof parser
 * @param {http.IncomingMessage} request    The HTTP request to this server.
 * @returns {EntityData} An object with `status` and `summary` members.
 */
parser.parseRequest = function(request) {
    var items = request.body.split(/^\*+$/m);
    return { status: items[0], summary: items[1] };
};


/**
 * Parses Sanity Check report to extract an object whose members are NGSI context attributes.
 *
 * @function getContextAttrs
 * @memberof parser
 * @param {EntityData} data                 Object holding raw entity data.
 * @returns {Object} Context attributes.
 *
 * <code>Sample report with global status 'NOK':
 * [Tests: 20, Errors: 0, Failures: 0, Skipped: 1]
 *
 * REGION GLOBAL STATUS
 *
 * Key Test Cases list: [u'test_allocate_ip', u'test_deploy_instance']
 * Region list with that test cases as PASSED status:
 * NONE!!!!!!!
 *
 * *********************************
 *
 * REGION TEST SUMMARY REPORT: 
 *
 *  >> region1
 *  OK	 test_allocate_ip
 *  OK	 test_base_image_for_testing_exists
 *  OK	 test_cloud_init_aware_images
 *  OK	 test_create_keypair
 *  OK	 test_create_network_and_subnet
 *  OK	 test_create_router_external_network
 *  OK	 test_create_router_no_external_network
 *  OK	 test_create_router_no_external_network_and_add_network_port
 *  OK	 test_create_security_group_and_rules
 *  OK	 test_deploy_instance_with_network_and_associate_public_ip
 *  OK	 test_deploy_instance_with_networks_and_e2e_connection_using_public_ip
 *  N/A	 test_deploy_instance_with_networks_and_e2e_snat_connection
 *  OK	 test_deploy_instance_with_new_network
 *  OK	 test_deploy_instance_with_new_network_and_all_params
 *  OK	 test_deploy_instance_with_new_network_and_keypair
 *  OK	 test_deploy_instance_with_new_network_and_metadata
 *  OK	 test_deploy_instance_with_new_network_and_sec_group
 *  OK	 test_external_networks
 *  OK	 test_flavors_not_empty
 *  OK	 test_images_not_empty
 * </code>
 *
 * <code>Sample report with global status 'NOK':
 * [Tests: 20, Errors: 0, Failures: 0, Skipped: 1]
 *
 * REGION GLOBAL STATUS
 *
 * Key Test Cases list: [u'test_allocate_ip', u'test_deploy_instance']
 * Region list with that test cases as PASSED status:
 *  >> region2
 *
 * *********************************
 *
 * REGION TEST SUMMARY REPORT: 
 *
 *  >> region2
 *  OK	 test_allocate_ip
 *  OK	 test_base_image_for_testing_exists
 *  NOK	 test_cloud_init_aware_images
 *  OK	 test_create_keypair
 *  OK	 test_create_network_and_subnet
 *  OK	 test_create_router_external_network
 *  OK	 test_create_router_no_external_network
 *  OK	 test_create_router_no_external_network_and_add_network_port
 *  OK	 test_create_security_group_and_rules
 *  OK	 test_deploy_instance_with_network_and_associate_public_ip
 *  OK	 test_deploy_instance_with_networks_and_e2e_connection_using_public_ip
 *  OK	 test_deploy_instance_with_networks_and_e2e_snat_connection
 *  OK	 test_deploy_instance_with_new_network
 *  OK	 test_deploy_instance_with_new_network_and_all_params
 *  OK	 test_deploy_instance_with_new_network_and_keypair
 *  OK	 test_deploy_instance_with_new_network_and_metadata
 *  OK	 test_deploy_instance_with_new_network_and_sec_group
 *  OK	 test_external_networks
 *  OK	 test_flavors_not_empty
 *  OK	 test_images_not_empty
 * </code>
 */
parser.getContextAttrs = function(probeEntityData) {
    var attrs = { sanity_status: 'N/A' };

    // Regions in which tests have been executed (must be exactly one)
    var summary = probeEntityData.summary.split('\n');
    var regions = summary.filter(function(item) {
        return item.match(/>>\s+\b\w+\b/);
    });
    if (regions.length != 1) {
        throw new Error('No single region sanity check summary report');
    }

    // Regions that passed key tests (must be zero or one)
    var passed = probeEntityData.status.split('\n').filter(function(item) {
        return item.match(/>>\s+\b\w+\b/);
    });
    attrs['sanity_status'] = (passed.length == 0) ? 'NOK' : 'OK';

    // Tests results
    summary.map(function(item) {
        var match = item.match(/\b(OK|NOK|N\/A)\b\s+\b(test_\w+)\b/),
            test_name = match && match[2],
            test_result = match && match[1];
        if (test_name && test_result) {
            attrs['sanity_' + test_name] = test_result;
        }
    });

    return attrs;
};


/**
 * Parser for sanity checks.
 */
exports.parser = parser;
