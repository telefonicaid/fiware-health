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
    http = require('http'),
    init = require('./init'),
    common = require('../../lib/routes/common'),
    refresh = require('../../lib/routes/refresh');


/* jshint unused: false */
suite('refresh', function () {

    test('test_get_refresh', function () {
        //given
        var req = sinon.stub(),
            res = sinon.stub();

        req.param = sinon.stub().returns('region1');
        req.session = sinon.stub();
        req.session.role = 'Admin';
        var requestStub = sinon.stub();
        var httpStub = sinon.stub(http, 'request').returns(requestStub);
        requestStub.on = sinon.stub();
        requestStub.write = sinon.stub();
        requestStub.end = sinon.stub();


        //when
        refresh.getRefresh(req, res);

        //then
        assert(requestStub.on.calledOnce);
        assert(requestStub.write.calledOnce);
        assert(requestStub.end.calledOnce);

        httpStub.restore();

    });


    test('test_get_refresh_with_undefined_role', function () {
        //given
        var req = sinon.stub(),
            res = sinon.stub();

        req.param = sinon.stub().returns('region1');
        req.session = sinon.stub();
        req.session.role = undefined;
        var commonStub = sinon.stub(common, 'notAuthorized');

        //when
        refresh.getRefresh(req, res);

        //then
        assert(commonStub.calledOnce);

        commonStub.restore();

    });
});

