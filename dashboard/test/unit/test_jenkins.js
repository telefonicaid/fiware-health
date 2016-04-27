/*
 * Copyright 2016 Telefónica I+D
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

'use strict';

var assert = require('assert'),
    cuid = require('cuid'),
    util = require('util'),
    init = require('./init'),
    logger = require('../../lib/logger'),
    config = require('../../lib/config').data,
    jenkinsApi = require('./init').jenkinsApi,
    jenkins = require('../../lib/jenkins');


/* jshint unused: false, camelcase: false */
suite('jenkins', function () {

    var stream = logger.stream;

    suiteSetup(function () {
        logger.stream = require('dev-null')();
        this.jobBuilds = [
            {
                number: 157,
                data: {
                    actions: [[{value: 'Region1'}]],
                    building: true
                }
            },
            {
                number: 158,
                data: {
                    actions: [[{value: 'Region2'}]],
                    building: false
                }
            }
        ];
    });

    suiteTeardown(function () {
        logger.stream = stream;
    });

    setup(function () {
        this.txid = cuid();
    });

    teardown(function () {
        delete this.txid;
    });

    test('should_initialize_jenkins_client_with_host_port_from_config', function () {
        var expectedJenkinsURL = util.format('http://%s:%d', config.jenkins.host, config.jenkins.port);
        assert(jenkinsApi.init.calledOnce);
        assert.equal(jenkinsApi.init.lastCall.args[0], expectedJenkinsURL);
    });

    test('should_invoke_callback_with_empty_params_if_job_info_fails', function (done) {
        //Given
        var jenkinsClient = jenkinsApi.init.lastCall.returnValue;

        jenkinsClient.job_info = function (jobName, result) {
            result('Some error');
        };

        //When
        jenkins.regionJobsInProgress(this.txid, function callback() {
            //Then
            assert.equal(arguments.length, 0);
            done();
        });
    });

    test('should_invoke_callback_with_build_status_of_all_jobs', function (done) {
        //Given
        var jenkinsBuilds = this.jobBuilds,
            jenkinsClient = jenkinsApi.init.lastCall.returnValue;

        jenkinsClient.job_info = function (jobName, result) {
            var jobBuilds = jenkinsBuilds.map(function(build) { return {number: build.number}; });
            result(null, {builds: jobBuilds});
        };

        jenkinsClient.build_info = function (jobName, buildNumber, result) {
            var buildData = jenkinsBuilds.filter(function(build) { return buildNumber === build.number; })[0].data;
            result(null, buildData);
        };

        //When
        jenkins.regionJobsInProgress(this.txid, function callback(progress) {
            //Then
            var buildParams = jenkinsBuilds.map(function(build) { return build.data.actions[0][0].value; });
            assert(progress);
            buildParams.forEach(function (param) {
                assert(progress.hasOwnProperty(param));
            });
            done();
        });
    });

});
