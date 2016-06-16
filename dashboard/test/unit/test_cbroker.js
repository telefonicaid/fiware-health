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

var fs = require('fs'),
    cuid = require('cuid'),
    assert = require('assert'),
    sinon = require('sinon'),
    http = require('http'),
    EventEmitter = require('events').EventEmitter,
    cbroker = require('../../lib/routes/cbroker'),
    constants = require('../../lib/constants'),
    logger = require('../../lib/logger'),
    config = require('../../lib/config').data,
    init = require('./init'),
    _ = require('underscore');


/**
 * @function isNaN
 * Assert that parameter is NaN
 * @param {number} value
 */
assert.isNaN = function (value) {
    assert.equal(value.toString(), 'NaN');
};


/* jshint unused: false, sub: true */
suite('cbroker', function () {

    var stream = logger.stream;

    suiteSetup(function () {
        logger.stream = require('dev-null')();
        this.sampleDataNotifyContext = fs.readFileSync('test/unit/notify_post1.json', 'utf8');
        this.sampleDataQueryContext = fs.readFileSync('test/unit/post1.json', 'utf8');
        this.parsedRegionsNotifyContext = [
            {
                node: 'Region2',
                status: constants.GLOBAL_STATUS_OK,
                timestamp: '2015/05/13 11:10 UTC',
                elapsedTime: '0h, 2m, 40s',
                elapsedTimeMillis: 160000
            }
        ];
        this.parsedRegionsQueryContext = [
            {
                node: 'Region2',
                status: constants.GLOBAL_STATUS_OK,
                timestamp: '2015/05/13 11:10 UTC',
                elapsedTime: '0h, 1m, 0s',
                elapsedTimeMillis: 60000
            },
            {
                node: 'Region3',
                status: constants.GLOBAL_STATUS_OTHER,
                timestamp: '2015/05/13 11:10 UTC',
                elapsedTime: '0h, 1m, 0s',
                elapsedTimeMillis: 60000
            },
            {
                node: 'Region4',
                status: constants.GLOBAL_STATUS_PARTIAL_OK,
                timestamp: '2015/05/13 11:10 UTC',
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            },
            {
                node: 'Region5',
                status: '',
                timestamp: '',
                elapsedTime: '',
                elapsedTimeMillis: ''
            },
            {
                node: 'Region6',
                status: '',
                timestamp: '',
                elapsedTime: '',
                elapsedTimeMillis: ''
            },
            {
                node: 'ZRegionLongName1',
                status: constants.GLOBAL_STATUS_NOT_OK,
                timestamp: '2015/05/13 11:10 UTC',
                elapsedTime: '0h, 2m, 40s',
                elapsedTimeMillis: 160000
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

    test('should_have_a_retrieveAllRegions_method', function () {
        assert.equal(cbroker.retrieveAllRegions.name, 'retrieveAllRegions');
    });

    test('should_return_a_json_with_all_regions_and_status', function () {
        //given
        var entities = JSON.parse(this.sampleDataQueryContext),
            expected = this.parsedRegionsQueryContext;

        //when
        cbroker.parseRegions(this.txid, entities);
        var result = config.regions.getRegions();

        //then
        assert.equal(expected[2].node, result[2].node);
        assert.isNaN(expected[2].elapsedTimeMillis);
        assert.isNaN(result[2].elapsedTimeMillis);
        assert(_.isEqual(expected, result));
    });

    test('should_receive_notify_from_context_broker_and_return_200_ok', function () {
        //given
        var data = this.sampleDataNotifyContext,
            expected = this.parsedRegionsNotifyContext[0],
            req = {
                body: data
            };

        //when
        var result = cbroker.getEntity(this.txid, req);

        //then
        assert.deepEqual(expected, result);
    });

    test('should_retrieve_data_about_all_regions', function (done) {
        //given
        var data = this.sampleDataQueryContext,
            index = 0,
            region = JSON.parse(data).contextResponses[index].contextElement.id,
            req = {
                param: sinon.stub(),
                session: {
                    user: {
                        email: 'user@mail.com'
                    }
                }
            };
        req.param.withArgs('region').returns(region);

        var request = new EventEmitter();
        request.setTimeout = sinon.spy();
        request.end = sinon.spy();
        request.write = sinon.spy();

        var requestStub = sinon.stub(http, 'request', function (options, callback) {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            response.emit('data', data);
            response.emit('end');
            return request;
        });

        //when
        cbroker.retrieveAllRegions(this.txid, function () {

            //then
            http.request.restore();
            assert.notEqual(config.regions.get(region), undefined);
            done();
        });

        assert(request.write.calledOnce);
        assert(request.end.calledOnce);
        assert(request.setTimeout.calledOnce);
        assert.equal('POST', requestStub.getCall(0).args[0].method);
    });

    test('should_return_empty_collection_when_an_error_occurs', function (done) {
        //given
        var req = {
                param: sinon.stub(),
                session: {
                    user: {
                        email: 'user@mail.com'
                    }
                }
            };
        req.param.withArgs('region').returns('some_region');

        var request = new EventEmitter();
        request.end = sinon.spy();
        request.write = sinon.spy();
        request.setTimeout = sinon.spy();

        var requestStub = sinon.stub(http, 'request', function (options, callback) {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            var errorString = '{ "errorCode" : { "reasonPhrase" : "Internal Server Error", ' +
                '"details" : "collection: .... exception: socket exception [FAILED_STATE] for localhost:27017"} }';

            response.emit('data', errorString);
            response.emit('end');
            return request;
        });

        //when
        cbroker.retrieveAllRegions(this.txid, function () {

            //then
            http.request.restore();
            done();
        });

        assert(request.write.calledOnce);
        assert(request.end.calledOnce);
        assert(request.setTimeout.calledOnce);
        assert.equal('POST', requestStub.getCall(0).args[0].method);
    });

    test('should_return_empty_region_list_and_print_log_when_timeout_on_request', function (done) {
        //given
        var data = this.sampleDataQueryContext,
            req = {
                param: sinon.stub(),
                session: {
                    user: {
                        email: 'user@mail.com'
                    }
                }
            };
        req.param.withArgs('region').returns('some_region');

        var request = new EventEmitter();
        request.setTimeout = sinon.spy(function (timeout, callback) {
            callback();
        });
        request.end = sinon.spy();
        request.write = sinon.spy();
        request.abort = sinon.spy(function () {
            this.emit('error', {code: 'ECONNRESET'});
        });

        var requestStub = sinon.stub(http, 'request', function () {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();
            response.emit('data', data);
            response.emit('end');
            return request;
        });

        //when
        cbroker.retrieveAllRegions(this.txid, function (result) {

            //then
            http.request.restore();
            assert.deepEqual(0, result.length);
            done();
        });

        assert(request.write.calledOnce);
        assert(request.end.calledOnce);
        assert(request.setTimeout.calledOnce);
        assert(request.abort.calledOnce);
        assert.equal('POST', requestStub.getCall(0).args[0].method);
    });

    test('should_return_empty_region_list_and_print_log_when_context_broker_is_down', function (done) {
        //given
        var data = this.sampleDataQueryContext,
            req = {
                param: sinon.stub(),
                session: {
                    user: {
                        email: 'user@mail.com'
                    }
                }
            };
        req.param.withArgs('region').returns('region1');

        var request = new EventEmitter();
        request.setTimeout = sinon.spy();
        request.end = sinon.spy(function () {
            this.emit('error', {code: 'ECONNREFUSED'});
        });
        request.write = sinon.spy();

        var requestStub = sinon.stub(http, 'request', function () {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();
            response.emit('data', data);
            response.emit('end');
            return request;
        });

        //when
        cbroker.retrieveAllRegions(this.txid, function (result) {

            //then
            http.request.restore();
            assert.deepEqual(0, result.length);
            done();
        });

        assert(request.write.calledOnce);
        assert(request.setTimeout.calledOnce);
        assert(request.end.calledOnce);
        assert.equal('POST', requestStub.getCall(0).args[0].method);
    });

    test('should_filter_region_list_and_remove_disabled_region', function () {
        //given
        var filtered = 'Region2',
            entities = JSON.parse(this.sampleDataQueryContext),
            expected = this.parsedRegionsQueryContext.filter(function (item) {
                return (item.node !== filtered);
            });
        config.cbroker.filter = [filtered];

        //when
        var result = cbroker.parseRegions(this.txid, entities);

        //then
        assert.equal(result.length, entities['contextResponses'].length - config.cbroker.filter.length);
        assert.equal(result.length, expected.length);
    });

});
