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
    cbroker = require('../../lib/routes/cbroker'),
    sinon = require('sinon'),
    EventEmitter = require('events').EventEmitter,
    http = require('http'),
    fs = require('fs');


/* jshint multistr: true */
suite('cbroker', function () {


    test('should_have_a_retrieveAllRegions_method', function () {
        assert.equal(cbroker.retrieveAllRegions.name, 'retrieveAllRegions');

    });

    test('should_return_a_json_with_all_regions_and_status', function () {
        //given
        var json = JSON.parse(fs.readFileSync('test/unit/post1.json', 'utf8'));
        var expected = [
            {node: 'Region1', status: 'NOK', timestamp: '2015/05/13 11:10 UTC', elapsedTime: '0h, 1m, 0s'},
            {node: 'Region2', status: 'OK', timestamp: '2015/05/13 11:10 UTC', elapsedTime: '0h, 1m, 0s'},
            {node: 'Region3', status: 'N/A', timestamp: '2015/05/13 11:10 UTC', elapsedTime: 'NaNh, NaNm, NaNs'},
            {node: 'Region4', status: 'POK', timestamp: '2015/05/13 11:10 UTC', elapsedTime: '0h, 1m, 0s'},
            {node: 'Region5', status: '', timestamp: '', elapsedTime: ''}


        ];

        //when
        var result = cbroker.parseRegions(json);
        //then

        assert.deepEqual(expected, result);

    });


    test('should_receive_notify_from_context_broker_and_return_200_ok', function () {
        //given

        var json = JSON.parse(fs.readFileSync('test/unit/notify_post1.json', 'utf8'));
        var expected = {'node': 'Region1', 'status': 'OK', 'timestamp': '', elapsedTime: ''};

        //when
        var result = cbroker.changeReceived(json);

        //then
        assert.deepEqual(expected, result);
    });

    test('should_retrieve_data_about_all_regions', function (done) {

        //given
        var req = sinon.stub();
        req.param = sinon.stub();
        req.param.withArgs('region').returns('region1');
        req.session = sinon.stub();
        req.session.user = {email: 'user@mail.com'};

        var request = new EventEmitter();

        request.setTimeout = sinon.spy();
        request.end = sinon.spy();
        request.write = sinon.spy();
        var requestStub = sinon.stub(http, 'request', function (options, callback) {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            var json = fs.readFileSync('test/unit/notify_post1.json', 'utf8');

            response.emit('data', json);
            response.emit('end');
            return request;
        });

        //when
        cbroker.retrieveAllRegions(function (result) {

            //then
            http.request.restore();
            assert.deepEqual('Region1', result[0].node);
            done();
        });

        assert(request.write.calledOnce);
        assert(request.end.calledOnce);
        assert(request.setTimeout.calledOnce);
        assert.equal('POST', requestStub.getCall(0).args[0].method);

    });

    test('should_return_empty_collection_when_an_error_occurs', function (done) {
        //given

        var req = sinon.stub();
        req.param = sinon.stub();
        req.param.withArgs('region').returns('region1');
        req.session = sinon.stub();
        req.session.user = {email: 'user@mail.com'};

        var request = new EventEmitter();

        request.end = sinon.spy();
        request.write = sinon.spy();
        request.setTimeout = sinon.spy();
        var requestStub = sinon.stub(http, 'request', function (options, callback) {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            var resultString = '{ "errorCode" : { "reasonPhrase" : "Internal Server Error", ' +
                '"details" : "collection: .... exception: socket exception [FAILED_STATE] for localhost:27017"} }';

            response.emit('data', resultString);
            response.emit('end');
            return request;
        });

        //when
        cbroker.retrieveAllRegions(function (result) {

            //then
            http.request.restore();
            assert.deepEqual([], result);
            done();
        });

        assert(request.write.calledOnce);
        assert(request.end.calledOnce);
        assert(request.setTimeout.calledOnce);
        assert.equal('POST', requestStub.getCall(0).args[0].method);
    });
    

    test('should_return_empty_region_list_and_print_log_when_timeout_on_request', function (done) {

        //given
        var req = sinon.stub();
        req.param = sinon.stub();
        req.param.withArgs('region').returns('region1');
        req.session = sinon.stub();
        req.session.user = {email: 'user@mail.com'};

        var request = new EventEmitter();

        request.setTimeout = sinon.spy(function (timeout, callback) {
                callback();
        });
        request.end = sinon.spy();
        request.write = sinon.spy();
        request.abort = sinon.spy(function () {
            var e = sinon.spy();
            e.code = 'ECONNRESET';
            this.emit('error', e);
        });
        var requestStub = sinon.stub(http, 'request', function () {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            var json = fs.readFileSync('test/unit/notify_post1.json', 'utf8');

            response.emit('data', json);
            response.emit('end');
            return request;
        });

        //when
        cbroker.retrieveAllRegions(function (result) {

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


});
