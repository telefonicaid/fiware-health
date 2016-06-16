/*
 * Copyright 2015-2016 Telefónica I+D
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
    init = require('./init'),
    app = require('../../lib/app'),
    monasca = require('../../lib/monasca'),
    cbroker = require('../../lib/routes/cbroker'),
    subscribe = require('../../lib/routes/subscribe'),
    common = require('../../lib/routes/common'),
    logger = require('../../lib/logger'),
    constants = require('../../lib/constants');


/* jshint unused: false */
suite('app', function () {

    var stream = logger.stream;

    suiteSetup(function () {
        logger.stream = require('dev-null')();
    });

    suiteTeardown(function () {
        logger.stream = stream;
    });

    setup(function () {
        this.request = {headers: []};
        this.response = {};
    });

    teardown(function () {
        delete this.request;
        delete this.response;
    });

    test('should_have_some_methods', function () {
        assert.equal(app.postContextBroker.name, 'postContextBroker');
        assert.equal(app.getLogout.name, 'getLogout');
    });

    test('should_return_400_in_contextbroker_post_with_exception_in_parser', function () {
        //given
        var req = this.request,
            res = this.response;

        res.send = sinon.spy();
        res.status = sinon.stub();
        res.status.withArgs(400).returns(res);

        var getEntityStub = sinon.stub(cbroker, 'getEntity');
        getEntityStub.throws();

        //when
        app.postContextBroker(req, res);

        //then
        getEntityStub.restore();
        assert(res.status.withArgs(400).calledOnce);
        assert(res.send.calledOnce);
    });

    test('should_only_notify_mailman_in_contextbroker_post_for_sanity_status_change', function () {
        //given
        var req = this.request,
            res = this.response;

        res.end = sinon.spy();
        res.status = sinon.stub();
        res.status.withArgs(200).returns(res);
        req.path = '/' + constants.CONTEXT_SANITY_STATUS_CHANGE;

        var mailmanNotifyStub = sinon.stub(subscribe, 'notify'),
            monascaNotifyStub = sinon.stub(monasca, 'notify'),
            getEntityStub = sinon.stub(cbroker, 'getEntity', function () {
                return {'node': 'Region1', 'status': 'OK', 'timestamp': ''};
            });

        //when
        app.postContextBroker(req, res);

        //then
        mailmanNotifyStub.restore();
        monascaNotifyStub.restore();
        getEntityStub.restore();
        assert(res.status.withArgs(200).calledOnce);
        assert(mailmanNotifyStub.calledOnce);
        assert(monascaNotifyStub.notCalled);
    });

    test('should_only_notify_monasca_in_contextbroker_post_for_sanity_status_value', function () {
        //given
        var req = this.request,
            res = this.response;

        res.end = sinon.spy();
        res.status = sinon.stub();
        res.status.withArgs(200).returns(res);
        req.path = '/' + constants.CONTEXT_SANITY_STATUS_VALUE;

        var mailmanNotifyStub = sinon.stub(subscribe, 'notify'),
            monascaNotifyStub = sinon.stub(monasca, 'notify'),
            getEntityStub = sinon.stub(cbroker, 'getEntity', function () {
                return {'node': 'Region1', 'status': 'OK', 'timestamp': ''};
            });

        //when
        app.postContextBroker(req, res);

        //then
        mailmanNotifyStub.restore();
        monascaNotifyStub.restore();
        getEntityStub.restore();
        assert(res.status.withArgs(200).calledOnce);
        assert(mailmanNotifyStub.notCalled);
        assert(monascaNotifyStub.calledOnce);
    });

    test('should_not_notify_at_all_in_contextbroker_post_when_region_status_excluded', function () {
        //given
        var req = this.request,
            res = this.response;

        res.end = sinon.spy();
        res.status = sinon.stub();
        res.status.withArgs(200).returns(res);

        var mailmanNotifyStub = sinon.stub(subscribe, 'notify'),
            monascaNotifyStub = sinon.stub(monasca, 'notify'),
            getEntityStub = sinon.stub(cbroker, 'getEntity', function () {
                return {'node': 'Region1', 'status': constants.GLOBAL_STATUS_OTHER, 'timestamp': ''};
            });

        //when
        app.postContextBroker(req, res);

        //then
        mailmanNotifyStub.restore();
        monascaNotifyStub.restore();
        getEntityStub.restore();
        assert(res.status.withArgs(200).calledOnce);
        assert(mailmanNotifyStub.notCalled);
        assert(monascaNotifyStub.notCalled);
    });

    test('should_close_session_with_get_logout', function () {
        //given
        var req = this.request,
            res = this.response;

        req.session = {};
        res.redirect = sinon.spy();
        res.clearCookie = sinon.spy();

        //when
        app.getLogout(req, res);

        //then
        assert(res.redirect.calledOnce);
        assert.equal(undefined, req.session.user);
        assert.equal(undefined, req.session.role);
        assert(res.clearCookie.calledWith('oauth_token'));
        assert(res.clearCookie.calledWith('expires_in'));
    });

    test('should_signin_with_token_in_get_signin', function () {
        //given
        var req = this.request,
            res = this.response;

        req.session = {accessToken: '756cfb31e062216544215f54447e2716'};

        var oa = {get: sinon.stub()};

        //when
        app.getSignin(req, res, oa);

        //then
        assert(oa.get.calledOnce);
    });

    test('should_signin_without_token_in_get_signin', function () {
        //given
        var req = this.request,
            res = this.response;

        req.session = {};
        res.redirect = sinon.stub();

        var path = 'http://localhost/oauth2',
            oa = {getAuthorizeUrl: sinon.stub().returns(path)};

        //when
        app.getSignin(req, res, oa);

        //then
        assert(oa.getAuthorizeUrl.calledOnce);
        assert(res.redirect.withArgs(path).calledOnce);
    });

    test('should_check_token_with_valid_token', function () {
        //given
        var req = this.request,
            res = this.response;

        var next = sinon.stub();

        req.session = {accessToken: '12123123123123'};

        //when
        app.checkToken(req, res, next, 'debug message');

        //then
        assert(next.calledOnce);
    });

    test('should_check_token_with_invalid_token', function () {
        //given
        var req = this.request,
            res = this.response;

        var next = sinon.stub();

        req.session = {accessToken: undefined};

        var commonStub = sinon.stub(common, 'notAuthorized');

        //when
        app.checkToken(req, res, next, 'debug message');

        //then
        assert(commonStub.calledOnce);
        commonStub.restore();
    });

    test('should_getAuthAccessToken_in_get_login', function () {
        //given
        var req = this.request,
            res = this.response;

        req.query = {code: 'code'};

        var oa = {getOAuthAccessToken: sinon.stub()};

        //when
        app.getLogin(req, res, oa);

        //then
        assert(oa.getOAuthAccessToken.calledOnce);
    });

    test('should_redirect_without_results_getOAuthAccessToken_callback', function () {
        //given
        var req = this.request,
            res = this.response,
            results;

        res.redirect = sinon.spy();

        var oauth2 = sinon.stub();

        //when
        app.getOAuthAccessTokenCallback(results, req, res, oauth2);

        //then
        assert(res.redirect.calledOnce);
    });

    test('should_call_to_oauth2_get_in_getOAuthAccessToken_callback', function () {
        //given
        var req = this.request,
            res = this.response,
            results = {accessToken: '13123213123123'};

        req.session = {};
        res.redirect = sinon.spy();

        var oauth2 = {get: sinon.stub()};

        //when
        app.getOAuthAccessTokenCallback(results, req, res, oauth2);

        //then
        assert(oauth2.get.calledOnce);
    });

    test('should_parse_and_redirect_oauth_get_callback', function () {
        //given
        var req = this.request,
            res = this.response;

        req.session = {};
        res.redirect = sinon.spy();

        var response = '{"organizations": [], "displayName": "kk@domain.com", "roles": ' +
            '[{"name": "Admin", "id": "123123dd"}, {"name": "Superuser", "id": "123123231"}],' +
            '"app_id": "1231231321321", "email": "kk@domain.com", "id": "123123123123"}';

        //when
        app.oauthGetCallback(response, req, res);

        //then
        assert(res.redirect.calledOnce);
        assert.equal(req.session.role, 'superuser');
    });

    test('should_reset_and_redirect_in_oauth_get_callback', function () {
        //given
        var req = this.request,
            res = this.response;

        req.session = {};
        res.redirect = sinon.spy();

        var response;

        //when
        app.oauthGetCallback(response, req, res);

        //then
        assert(res.redirect.calledOnce);
        assert.equal(req.session.user, undefined);
        assert.equal(req.session.role, undefined);
        assert.equal(req.session.accessToken, undefined);
    });


});
