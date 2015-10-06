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
    subscribe = require('../../lib/routes/subscribe'),
    sinon = require('sinon'),
    http = require('http'),
    EventEmitter = require('events').EventEmitter,
    logger = require('../../lib/logger');



/* jshint multistr: true */
suite('subscribe', function () {

    suiteSetup(function() {
        logger.setLevel('ERROR');
    });

    teardown(function() {
        http.request.restore();
    });

    test('should_searchSubscription_in_regions_list', function (done) {


        //given
        var user = 'user@mail.com';
        var regions = [
            {node: 'region1', status: 'N/A'},
            {node: 'region2', status: 'OK'}
        ];

        var emailList = [
            '["user@mail.com","user2@mail.com"]',
            '[]'
        ];

         sinon.stub(http, 'request', function(options, callback) {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            response.emit('data', emailList[http.request.callCount - 1]);
            response.emit('end');
            var request = new EventEmitter();
            request.end = sinon.spy();
            return request;
        });



        //when
        subscribe.searchSubscription(user, regions, function () {
            assert(regions[0].subscribed);
            assert(!regions[1].subscribed);
            done();
        });
        //then


    });

    test('should_add_subscribed_to_true_in_isSubscribed_with_user_subscribed', function (done) {
        //given
        var user = 'user@mail.com';
        var region = {node: 'region1'};

         sinon.stub(http, 'request', function(options, callback) {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            response.emit('data', '["user@mail.com","user2@mail.com"]');
            response.emit('end');
            var request = new EventEmitter();
            request.end = sinon.spy();
            return request;
        });

        //when
        subscribe.isSubscribed(user, region, function () {
            assert(region.subscribed);
            done();
        });
        //then


    });

    test('should_add_subscribed_to_false_in_isSubscribed_with_user_not_subscribed', function (done) {
        //given
        var user = 'kk@mail.com';
        var region = {node: 'region1'};


         sinon.stub(http, 'request', function(options, callback) {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            response.emit('data', '["user@mail.com"]');
            response.emit('end');
            var request = new EventEmitter();
            request.end = sinon.spy();
            return request;
        });

        //when
        subscribe.isSubscribed(user, region, function () {
            assert(!region.subscribed);
            done();
        });
        //then


    });

    test('should_add_subscribed_to_false_in_isSubscribed_with_unknown_region', function (done) {
        //given
        var user = 'kk@mail.com';
        var region = {node: 'unknown'};

        sinon.stub(http, 'request', function(options, callback) {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            response.emit('data', '[]');    //with undefined region, mailman return empty list
            response.emit('end');
            var request = new EventEmitter();
            request.end = sinon.spy();
            return request;
        });
        //when
        subscribe.isSubscribed(user, region, function () {
            assert(!region.subscribed);
            done();
        });
        //then


    });

    test('should_subcribe_user_and_redirect_to_webcontext', function () {

        //given
        var req, res, spy;
        req = sinon.stub();
        res = {};
        req.param = sinon.stub();
        req.param.withArgs('region').returns('region1');
        spy = res.redirect = sinon.spy();
        req.session = sinon.stub();
        req.session.user = {email: 'user@mail.com'};

        var request = new EventEmitter();

        request.end = sinon.spy();
        request.write = sinon.spy();
        var requestStub = sinon.stub(http, 'request', function(options, callback) {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            response.emit('end');
            return request;
        });

        //when
        subscribe.getSubscribe(req, res);

        //then
        assert(spy.calledOnce);
        assert(request.write.calledOnce);
        assert(request.end.calledOnce);
        assert.equal('PUT', requestStub.getCall(0).args[0].method);


    });


    test('should_notify_to_list', function () {

        //given
        var req;
        req = sinon.stub();
        req.param = sinon.stub();
        req.param.withArgs('region').returns('region1');
        req.session = sinon.stub();
        req.session.user = {email: 'user@mail.com'};

        var request = new EventEmitter();

        request.end = sinon.spy();
        request.write = sinon.spy();
        var requestStub = sinon.stub(http, 'request', function(options, callback) {

            var response = new EventEmitter();
            response.setEncoding = sinon.stub();

            callback(response);

            response.emit('end');
            return request;
        });

        //when
        subscribe.notify('region1', function() {
        });

        //then
        assert(request.write.calledOnce);
        assert(request.end.calledOnce);
        assert.equal('POST', requestStub.getCall(0).args[0].method);


    });

});
