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
    EventEmitter = require('events').EventEmitter,
    http = require('http'),
    init = require('./init'),
    unsubscribe = require('../../lib/routes/unsubscribe');


/* jshint unused: false */
suite('unsubscribe', function () {


    test('should_unsubcribe_user_and_redirect_to_webcontext', function () {

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

            response.emit('data', '[]');
            response.emit('end');
            return request;
        });

        //when
        unsubscribe.getUnSubscribe(req, res);

        //then
        assert(spy.calledOnce);
        assert(request.write.calledOnce);
        assert(request.end.calledOnce);
        assert.equal('DELETE', requestStub.getCall(0).args[0].method);

        http.request.restore();


    });

});
