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
    url = require('url'),
    cuid = require('cuid'),
    init = require('./init'),
    logger = require('../../lib/logger'),
    config = require('../../lib/config').data,
    jenkinsApi = require('./init').jenkinsApi,
    jenkins = require('../../lib/jenkins');


/* jshint unused: false, camelcase: false, sub: true */
suite('jenkins', function () {

    var stream = logger.stream;

    suiteSetup(function () {
        logger.stream = require('dev-null')();

        var jobParameters = [
            {name: 'ENVIRONMENT', value: 'fiwarelab'},
            {name: 'JENKINS_USER', value: 'user'},
            {name: 'JENKINS_PASSWORD'}
        ];

        this.regionParamName = config.jenkins.parameterName || 'OS_REGION_NAME';

        this.jobProgress = {
            'Region1': true,
            'Region2': false
        };

        this.jobBuildsJenkins1_5 = [
            {
                number: 157,
                data: {
                    building: this.jobProgress['Region1'],
                    actions: [
                        {
                            parameters: jobParameters.concat([{name: this.regionParamName, value: 'Region1'}])
                        }
                    ]
                }
            },
            {
                number: 158,
                data: {
                    building: this.jobProgress['Region2'],
                    actions: [
                        {
                            parameters: jobParameters.concat([{name: this.regionParamName, value: 'Region2'}])
                        }
                    ]
                }
            }
        ];

        this.jobBuildsJenkins1_6 = [
            {
                number: 157,
                data: {
                    building: this.jobProgress['Region1'],
                    actions: [
                        jobParameters.concat([{name: this.regionParamName, value: 'Region1'}])
                    ]
                }
            },
            {
                number: 158,
                data: {
                    building: this.jobProgress['Region2'],
                    actions: [
                        jobParameters.concat([{name: this.regionParamName, value: 'Region2'}])
                    ]
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

    test('should_add_to_config_calculated_jenkins_url', function () {
        var jenkinsContext = config.jenkins.path.replace(/(.*)\/job\/.+/, '$1'),
            expectedJenkinsURL = url.format({
                protocol: 'http',
                pathname: jenkinsContext,
                hostname: config.jenkins.host,
                port: config.jenkins.port
            });
        assert(config.jenkins.hasOwnProperty('url'));
        assert.equal(config.jenkins.url, expectedJenkinsURL);
    });

    test('should_initialize_jenkins_client_with_url_from_config', function () {
        var expectedJenkinsURL = config.jenkins.url;
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

    test('should_invoke_callback_with_build_status_of_all_jobs_in_jenkins_1_5', function (done) {
        //Given
        var jenkinsClient = jenkinsApi.init.lastCall.returnValue,
            jenkinsBuilds = this.jobBuildsJenkins1_5,
            jenkinsJobProgress = this.jobProgress;

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
            assert(progress);
            for (var region in jenkinsJobProgress) {
                assert(progress.hasOwnProperty(region));
                assert.equal(progress[region], jenkinsJobProgress[region]);
            }
            done();
        });
    });

    test('should_invoke_callback_with_build_status_of_all_jobs_in_jenkins_1_6', function (done) {
        //Given
        var jenkinsClient = jenkinsApi.init.lastCall.returnValue,
            jenkinsBuilds = this.jobBuildsJenkins1_6,
            jenkinsJobProgress = this.jobProgress;

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
            assert(progress);
            for (var region in jenkinsJobProgress) {
                assert(progress.hasOwnProperty(region));
                assert.equal(progress[region], jenkinsJobProgress[region]);
            }
            done();
        });
    });

});
