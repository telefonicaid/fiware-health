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
    OAuth2 = require('../../lib/oauth2').OAuth2;




/* jshint multistr: true */
suite('oauth2', function () {


    test('should_return_token_url', function () {

        //given
        var oa = new OAuth2('id',
                'secret',
                'http://idm',
                '/oauth2/authorize',
                '/oauth2/token',
                'http://idm/callback');

        //when
        var result = oa._getAccessTokenUrl();

        //then
        assert.equal(result, 'http://idm/oauth2/token');

    });

    test('should_set_token_name', function () {

        //given
        var oa = new OAuth2('id',
                'secret',
                'http://idm',
                '/oauth2/authorize',
                '/oauth2/token',
                'http://idm/callback');

        //when
        oa.setAccessTokenName('name1');

        //then
        assert.equal(oa._accessTokenName, 'name1');

    });

    test('test_buildAuthHeader', function () {

        //given
        var oa = new OAuth2('id',
                'secret',
                'http://idm',
                '/oauth2/authorize',
                '/oauth2/token',
                'http://idm/callback');

        //when
        oa.buildAuthHeader();

        //then
        assert.equal(oa._authMethod, 'Basic');

    });

    test('test_getOAuthAccessToken', function () {

        //given
        var oa = new OAuth2('id',
                'secret',
                'http://idm',
                '/oauth2/authorize',
                '/oauth2/token',
                'http://idm/callback');

        var code = 200;
        var callback = sinon.stub();

        var requestStub = sinon.stub(oa, '_request');

        //when
        oa.getOAuthAccessToken(code, callback);

        //then
        assert(requestStub.calledOnce);
        requestStub.restore();

    });

    test('test_getOAuthAccessToken_request', function () {

        //given
        var oa = new OAuth2('id',
                'secret',
                'http://idm',
                '/oauth2/authorize',
                '/oauth2/token',
                'http://idm/callback');

        var error = true;
        var callbackStub = sinon.stub();
        var data = sinon.stub();

        //when
        /*jshint camelcase: false */
        oa._getOAuthAccessToken_request(error, callbackStub, data);

        //then
        assert(callbackStub.withArgs(true).calledOnce);

    });


    test('test_getOAuthAccessToken_request_with_error_false_and_json', function () {

        //given
        var oa = new OAuth2('id',
                'secret',
                'http://idm',
                '/oauth2/authorize',
                '/oauth2/token',
                'http://idm/callback');

        var error = false;
        var callbackStub = sinon.stub();
        var data = '{"a":"b", "c":"d"}';

        //when
        /*jshint camelcase: false */
        oa._getOAuthAccessToken_request(error, callbackStub, data);

        //then
        assert(callbackStub.withArgs(null, { a: 'b', c: 'd' }).calledOnce);

    });

    test('test_getOAuthAccessToken_request_with_error_false_and_querystring', function () {

        //given
        var oa = new OAuth2('id',
                'secret',
                'http://idm',
                '/oauth2/authorize',
                '/oauth2/token',
                'http://idm/callback');

        var error = false;
        var callbackStub = sinon.stub();
        var data = 'a=b&c=d';

        //when
        /*jshint camelcase: false */
        oa._getOAuthAccessToken_request(error, callbackStub, data);

        //then
        assert(callbackStub.withArgs(null, { a: 'b', c: 'd' }).calledOnce);

    });

    test('test_request', function () {

        //given
        var oa = new OAuth2('id',
                'secret',
                'http://idm',
                '/oauth2/authorize',
                '/oauth2/token',
                'http://idm/callback');
        var method = sinon.stub();
        var url = 'http://localhost';
        var headers = '';
        var postBody = '';
        var accessToken = '123132131223123';
        var callback = sinon.stub();
        var httpStub = sinon.stub(http, 'request');
        var requestStub = sinon.stub();
        httpStub.returns(requestStub);

        requestStub.on = sinon.stub();
        requestStub.end = sinon.stub();

        //when

        try {
            oa._request(method, url, headers, postBody, accessToken, callback);

            //then

        } finally {

            httpStub.restore();
        }


    });

});
