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
    monasca = require('../../lib/monasca'),
    sinon = require('sinon'),
    http = require('http'),
    EventEmitter = require('events').EventEmitter,
    logger = require('../../lib/logger');



/* jshint multistr: true, unused: false */
suite('monasca', function () {

    var stream = logger.stream;
    var region = {
        node: 'region1',
        status: 'OK',
        timestamp: '2015/05/13 11:10 UTC',
        elapsedTime: '0h, 1m, 0s',
        elapsedTimeMillis: 60000
    };

    suiteSetup(function () {
        logger.stream = require('dev-null')();
    });

    suiteTeardown(function () {
        logger.stream = stream;
    });

    test('should_notify_to_monasca_api', function () {
        //given
        var req;
        req = sinon.stub();
        req.param = sinon.stub();
        req.param.withArgs('region').returns(region.node);

        var request = new EventEmitter();

        request.end = sinon.spy();
        request.write = sinon.spy();
        var requestStub = sinon.stub(http, 'request', function (options, callback) {
            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            response.emit('end');
            return request;
        });

        var keystoneStub = sinon.stub(monasca, 'withAuthToken', function (callback) {
            callback('TOKEN');
        });

        var notifyError;

        //when
        monasca.notify(region, function (err) {
            notifyError = err;
        });

        //then
        http.request.restore();
        keystoneStub.restore();
        assert(request.write.calledOnce);
        assert(request.end.calledOnce);
        assert.equal(notifyError, undefined);
        assert.equal('POST', requestStub.getCall(0).args[0].method);
    });

    test('should_return_error_if_monasca_request_failed', function (done) {
        //given
        var req;
        req = sinon.stub();
        req.param = sinon.stub();
        req.param.withArgs('region').returns(region.node);

        var request = new EventEmitter();

        request.end = sinon.spy();
        request.write = sinon.spy();
        var requestStub = sinon.stub(http, 'request', function (options, callback) {
            process.nextTick(function () { request.emit('error', new Error('some error')); });
            return request;
        });

        var keystoneStub = sinon.stub(monasca, 'withAuthToken', function (callback) {
            callback('TOKEN');
        });

        //when
        monasca.notify(region, function (err) {
            http.request.restore();
            keystoneStub.restore();
            assert(err instanceof Error);
            done();
        });

        //then
    });

    test('should_return_error_if_keystone_failed', function (done) {
        //given
        var req;
        req = sinon.stub();
        req.param = sinon.stub();
        req.param.withArgs('region').returns(region.node);

        var request = new EventEmitter();
        request.setTimeout = sinon.spy();
        request.end = sinon.spy();
        request.write = sinon.spy();
        var requestStub = sinon.stub(http, 'request', function (options, callback) {
            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            response.emit('data', 'some data');
            response.statusCode = 500;
            response.emit('end');
            return request;
        });

        //when
        monasca.notify(region, function (err) {
            http.request.restore();
            assert(err instanceof Error);
            done();
        });

        //then
    });

    test('should_return_error_if_keystone_timed_out', function (done) {
        //given
        var req;
        req = sinon.stub();
        req.param = sinon.stub();
        req.param.withArgs('region').returns(region.node);

        var request = new EventEmitter();
        request.setTimeout = sinon.spy();
        request.write = sinon.spy();
        request.end = sinon.spy();
        var requestStub = sinon.stub(http, 'request', function (options, callback) {
            process.nextTick(function () { request.emit('error', {code: 'ECONNRESET'}); });
            return request;
        });

        //when
        monasca.notify(region, function (err) {
            http.request.restore();
            assert(err instanceof Error);
            done();
        });

        //then
    });

    test('should_return_error_if_no_auth_token_obtained', function (done) {
        //given
        var keystoneStub = sinon.stub(monasca, 'withAuthToken', function (callback) {
            callback();
        });

        //when
        monasca.notify(region, function (err) {
            keystoneStub.restore();
            assert(err instanceof Error);
            done();
        });

        //then
    });

});
