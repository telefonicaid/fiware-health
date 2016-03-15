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

var express = require('express'),
    session = require('express-session'),
    stylus = require('stylus'),
    nib = require('nib'),
    path = require('path'),
    // TODO favicon = require('serve-favicon'),
    cookieParser = require('cookie-parser'),
    bodyParser = require('body-parser'),
    index = require('./routes/index'),
    refresh = require('./routes/refresh'),
    subscribe = require('./routes/subscribe'),
    unsubscribe = require('./routes/unsubscribe'),
    cbroker = require('./routes/cbroker'),
    monasca = require('./routes/monasca'),
    common = require('./routes/common'),
    config = require('./config').data,
    logger = require('./logger'),
    OAuth2 = require('./oauth2').OAuth2,
    constants = require('./constants');


var app = express();


logger.info('Running app in web context: %s', config.webContext);

/**
 * base web context in url
 * @type {string}
 */
app.base = config.webContext;

/**
 * web context
 * @type {string}
 */
app.locals.webContext = config.webContext;
/**
 * contain title of web page
 * @type {string}
 */
app.locals.title = 'Sanity check status';


/**
 * compile stylus css on runtime
 * @param {String} str
 * @param {String} path
 * @return {*|Function}
 */
function compile(str, path) {
    return stylus(str)
        .set('filename', path)
        .use(nib())
        .define('logoImage', function() {
                return new stylus.nodes.Literal('url("' + config.webContext + 'images/logo.png")');
        });
}
/**
 * called when /contextbroker post
 * @param {*} req
 * @param {*} res
 */
function postContextbroker(req, res) {
     try {
        var region = cbroker.changeReceived(req.body),
            notifyExclude = [ constants.GLOBAL_STATUS_OTHER ];

        logger.info('status change notification received from contextbroker for region: %s', region.node);
        res.status(200).end();

        if (notifyExclude.indexOf(region.status) === -1) {
            subscribe.notify(region, function (err) {
                if (err) {
                    logger.error('post to mailing list failed: %s', err);
                } else {
                    logger.info('post to mailing list succeeded');
                }
            });
            monasca.notify(region, function (err) {
                if (err) {
                    logger.error('post to Monasca failed: %s', err);
                } else {
                    logger.info('post to Monasca succeeded');
                }
            });
        } else {
            logger.info('notifications to mailing list and Monasca not sent because region status %s is excluded',
                region.status);
        }

    } catch (ex) {
        logger.error('error in contextbroker notification: %s', ex);
        res.status(400).send({ error: 'bad request! ' + ex });
    }

}

/**
 * called when /logout get
 * @param {*} req
 * @param {*} res
 */
function getLogout(req, res) {
    req.session.accessToken = undefined;
    req.session.user = undefined;
    req.session.role = undefined;

    res.clearCookie('oauth_token');
    res.clearCookie('expires_in');

    res.redirect(config.webContext);
}


/**
 *
 * @param {*} response
 * @param {*} req
 * @param {*} res
 */
function oauthGetCallback(response, req, res) {
    logger.debug({op: 'app#get login'}, 'response get userinfo: ' + response);
    if (response !== undefined) {
        var user = JSON.parse(response);
        req.session.user = user;
        req.session.role = common.parseRoles(user.roles);
    } else {
        req.session.accessToken = undefined;
        req.session.user = undefined;
        req.session.role = undefined;
    }
    res.redirect(config.webContext);
}

/**
 * called when /signin get
 * @param {*} req
 * @param {*} res
 * @param {*} oauth2
 */
function getSignin(req, res, oauth2) {
    logger.debug({op: 'app#get signin'}, 'Token: %s', req.session.accessToken);

    // If auth_token is not stored in a session redirect to IDM
    if (!req.session.accessToken) {
        var path = oauth2.getAuthorizeUrl();
        logger.debug({op: 'app#get signin'}, 'idm path: %s', path);
        res.redirect(path);
        // If auth_token is stored in a session cookie it sends a button to get user info
    } else {

        oauth2.get(config.idm.url + '/user/', req.session.accessToken, function (e, response) {
            oauthGetCallback(response, req, res);

        });

    }
}

/**
 * check access token
 * @param {*} req
 * @param {*} res
 * @param {function} next
 * @param {String} debugMessage
 */
function checkToken(req, res, next, debugMessage) {
    logger.debug(debugMessage);
    if (req.session.accessToken) {

        next();
    } else {
        common.notAuthorized(req, res);
    }
}

/**
 *
 * @param {Object} results
 * @param {*} req
 * @param {*} res
 * @param {*} oauth2
 */

function getOAuthAccessTokenCallback(results, req, res, oauth2) {
    logger.debug({op: 'app#get login'}, 'get access token:' + results);

        if (results !== undefined) {

            // Stores the accessToken in a session cookie
            /*jshint camelcase: false */
            req.session.accessToken = results.access_token;

            logger.debug({op: 'app#get login'}, 'accessToken: ' + results.access_token);

            oauth2.get(config.idm.url + '/user/', results.access_token, function (e, response) {
                oauthGetCallback(response, req, res);
            });
        } else {
            res.redirect(config.webContext);

        }
}

/**
 * Handles requests from IDM with the access code
 * @param {*} req
 * @param {*} res
 * @param {*} oauth2
 */
function getLogin(req, res, oauth2) {

    logger.debug({op: 'app#get login'}, 'req:' + req.query.code);

    // Using the access code goes again to the IDM to obtain the accessToken
    oauth2.getOAuthAccessToken(req.query.code, function (e, results) {

        getOAuthAccessTokenCallback(results, req, res, oauth2);

    });
}


// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

// uncomment after placing your favicon in /public
//app.use(favicon(__dirname + '/public/favicon.ico'));

app.use(config.webContext, stylus.middleware(
    {
        src: __dirname + '/stylus',
        dest: __dirname + '/public/stylesheets',
        compile: compile
    }
));

app.use(session({secret: config.secret}));

// trace all requests
app.use(function (req, res, next) {
    logger.debug({op: 'app#use'}, '%s %s %s', req.method, req.url, req.path);
    next();
});


app.use(config.paths.reportsUrl, express.static(config.paths.reportsFiles));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(config.webContext, express.static(path.join(__dirname, 'public')));


app.use(config.webContext + 'refresh', function (req, res, next) {
    checkToken(req, res, next, 'Accessing to refresh');
}, refresh);

app.use(config.webContext + 'subscribe', function (req, res, next) {
    checkToken(req, res, next, 'Accessing to subscribe');

}, subscribe);

app.use(config.webContext + 'unsubscribe', function (req, res, next) {
    checkToken(req, res, next, 'Accessing to unSubscribe');

}, unsubscribe);


app.use(config.webContext, index);

//configure login with oAuth

// Creates oauth library object with the config data
var oa = new OAuth2(config.idm.clientId,
    config.idm.clientSecret,
    config.idm.url,
    '/oauth2/authorize',
    '/oauth2/token',
    config.idm.callbackURL);



app.get(config.webContext + 'signin', function (req, res) {
    getSignin(req, res, oa);
});


app.get(config.webContext + 'login', function (req, res) {

  getLogin(req, res, oa);

});

// listen request from contextbroker changes
app.post(config.webContext + 'contextbroker', function (req, res) {
   postContextbroker(req, res);
});


// Redirection to IDM authentication portal
app.get(config.webContext + 'auth', function (req, res) {
    var path = oa.getAuthorizeUrl();
    res.redirect(path);
});

// Handles logout requests to remove accessToken from the session cookie
app.get(config.webContext + 'logout', function (req, res) {

    getLogout(req, res);

});


// catch 404 and forward to error handler
app.use(function (req, res) {
    var err = new Error('Not Found');
    err.status = 404;
    res.render('error', {
        message: err.message,
        error: err,
        timestamp: req.session.titleTimestamp
    });

});


// error handlers

// production error handler
// no stacktraces leaked to user
app.use(function (err, req, res) {
    res.status(err.status || 500);
    res.render('error', {
        timestamp: req.session.titleTimestamp,
        message: err.message,
        error: {}
    });
});


/** @export */
module.exports = app;


/** @export */
module.exports.postContextbroker = postContextbroker;

/** @export */
module.exports.getLogout = getLogout;

/** @export */
module.exports.getSignin = getSignin;

/** @export */
module.exports.getLogin = getLogin;

/** @export */
module.exports.checkToken = checkToken;

/** @export */
module.exports.getOAuthAccessTokenCallback = getOAuthAccessTokenCallback;

/** @export */
module.exports.oauthGetCallback = oauthGetCallback;
