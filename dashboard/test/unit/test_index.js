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

'use strict';

var assert = require('assert'),
    sinon = require('sinon'),
    logger = require('../../lib/logger'),
    jenkinsApi = require('./init').jenkinsApi,
    jenkins = require('../../lib/jenkins'),
    cbroker = require('../../lib/routes/cbroker'),
    index = require('../../lib/routes/index');


/* jshint unused: false */
suite('index', function () {

    var stream = logger.stream;

    suiteSetup(function () {
        logger.stream = require('dev-null')();
        this.jenkinsStub = sinon.stub(jenkins, 'regionJobsInProgress', function (txid, callback) {
            callback();
        });
    });

    suiteTeardown(function () {
        logger.stream = stream;
        this.jenkinsStub.restore();
    });

    setup(function () {
        this.request = {headers: []};
        this.response = {};
    });

    teardown(function () {
        delete this.request;
        delete this.response;
    });

    test('test_get_index', function () {
        //given
        var req = this.request,
            res = this.response,
            cbrokerStub = sinon.stub(cbroker, 'retrieveAllRegions');

        //when
        index.getIndex(req, res);

        //then
        cbrokerStub.restore();
        assert(cbrokerStub.calledOnce);
    });

    test('should_retrieveAllRegions_with_empty_region_list', function () {
        //given
        var req = this.request,
            res = this.response,
            cbrokerStub = sinon.stub(cbroker, 'retrieveAllRegions', function (txid, callback) {
                req.session = {user: undefined};
                res.render = sinon.spy();
                callback([]);
            });

        //when
        index.getIndex(req, res);

        //then
        cbrokerStub.restore();
        assert(cbrokerStub.calledOnce);
        assert(res.render.calledOnce);
    });

    test('should_retrieveAllRegions_with_empty_region_list_and_user_logged', function () {
        //given
        var req = this.request,
            res = this.response,
            cbrokerStub = sinon.stub(cbroker, 'retrieveAllRegions', function (txid, callback) {
                req.session = {user: {displayName: 'name01'}};
                res.render = sinon.spy();
                callback();
            });

        //when
        index.getIndex(req, res);

        //then
        cbrokerStub.restore();
        assert(cbrokerStub.calledOnce);
    });

});
