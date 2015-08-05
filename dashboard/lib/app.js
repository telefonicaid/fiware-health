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
    common = require('./routes/common'),
    config = require('./config').data,
    logger = require('./logger'),
    dateFormat = require('dateformat'),
    OAuth2 = require('./oauth2').OAuth2;


var app = express();


logger.info('Running app in web context: %s', config.web_context);

/**
 * base web context in url
 * @type {string}
 */
app.base = config.web_context;

/**
 * web context
 * @type {string}
 */
app.locals.web_context = config.web_context;
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
                return new stylus.nodes.Literal('url("' + config.web_context + 'images/logo.png")');
        });
}
/**
 * called when /contextbroker get
 * @param {*} req
 * @param {*} res
 */
function post_contextbroker(req, res) {
     try {
        var region = cbroker.changeReceived(req.body);
        logger.info('request received from contextbroker for region: %s', region.node);
        subscribe.notify(region.node, function () {
            logger.info('post to list ok');

            res.status(200).end();
        });
    } catch (ex) {
        logger.error('error in contextbroker notification: %s', ex);
        res.status(400).send({ error: 'bad request! ' + ex });
    }

}

/**
 * called when /logout get
 * @param req
 * @param res
 */
function get_logout(req, res) {
    req.session.access_token = undefined;
    req.session.user = undefined;
    req.session.role = undefined;

    res.clearCookie('oauth_token');
    res.clearCookie('expires_in');

    res.redirect(config.web_context);
}

/**
 * called when /signin get
 * @param req
 * @param res
 */
function get_signin(req, res, oauth2) {
    logger.debug({op: 'app#get signin'}, 'Token: %s', req.session.access_token);

    // If auth_token is not stored in a session redirect to IDM
    if (!req.session.access_token) {
        var path = oauth2.getAuthorizeUrl();
        logger.debug({op: 'app#get signin'}, 'idm path: %s', path);
        res.redirect(path);
        // If auth_token is stored in a session cookie it sends a button to get user info
    } else {

        oauth2.get(config.idm.url + '/user/', req.session.access_token, function (e, response) {
            oauth_get_callback(response,req, res);

        });

    }
}

/**
 * check access token
 * @param req
 * @param res
 * @param next
 * @param debug_message
 */
function check_token(req, res, next, debug_message) {
    logger.debug(debug_message);
    if (req.session.access_token) {

        next();
    } else {
        common.notAuthorized(req, res);
    }
}

/**
 *
 * @param response
 * @param req
 * @param res
 */
function oauth_get_callback(response, req, res) {
    logger.debug({op: 'app#get login'}, 'response get userinfo: ' + response);
    if (response != undefined) {
        var user = JSON.parse(response);
        req.session.user = user;
        req.session.role = common.parseRoles(user.roles);
    } else {
        req.session.access_token = undefined;
        req.session.user = undefined;
        req.session.role = undefined;
    }
    res.redirect(config.web_context);
}

/**
 *
 * @param results
 * @param req
 * @param res
 * @param oauth2
 */

function getOAuthAccessToken_callback(results, req, res, oauth2) {
    logger.debug({op: 'app#get login'}, 'get access token:' + results);

        if (results != undefined) {

            // Stores the access_token in a session cookie
            req.session.access_token = results.access_token;

            logger.debug({op: 'app#get login'}, 'access_token: ' + results.access_token);

            oauth2.get(config.idm.url + '/user/', results.access_token, function (e, response) {
                oauth_get_callback(response, req, res);
            });
        } else {
            res.redirect(config.web_context);

        }
}

/**
 * Handles requests from IDM with the access code
 *
 */
function get_login(req, res, oauth2) {

    logger.debug({op: 'app#get login'}, 'req:' + req.query.code);

    // Using the access code goes again to the IDM to obtain the access_token
    oauth2.getOAuthAccessToken(req.query.code, function (e, results) {

        getOAuthAccessToken_callback(results, req, res, oauth2);

    });
}


// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

// uncomment after placing your favicon in /public
//app.use(favicon(__dirname + '/public/favicon.ico'));

app.use(config.web_context, stylus.middleware(
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


app.use(config.paths.reports_url, express.static(config.paths.reports_files));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(config.web_context, express.static(path.join(__dirname, 'public')));


app.use(config.web_context + 'refresh',function (req, res, next) {
    check_token(req, res, next, 'Accessing to refresh');
}, refresh);

app.use(config.web_context + 'subscribe', function (req, res, next) {
    check_token(req, res, next, 'Accessing to subscribe');

}, subscribe);

app.use(config.web_context + 'unsubscribe', function (req, res, next) {
    check_token(req, res, next, 'Accessing to unSubscribe');

}, unsubscribe);


app.use(config.web_context, index);

//configure login with oAuth

// Creates oauth library object with the config data
var oa = new OAuth2(config.idm.clientId,
    config.idm.clientSecret,
    config.idm.url,
    '/oauth2/authorize',
    '/oauth2/token',
    config.idm.callbackURL);



app.get(config.web_context + 'signin', function (req, res) {
    get_signin(req, res, oa);
});


app.get(config.web_context + 'login', function (req, res) {

  get_login(req, res, oa);

});

// listen request from contextbroker changes
app.post(config.web_context + 'contextbroker', function (req, res) {
   post_contextbroker(req,res);
});


// Redirection to IDM authentication portal
app.get(config.web_context + 'auth', function (req, res) {
    var path = oa.getAuthorizeUrl();
    res.redirect(path);
});

// Handles logout requests to remove access_token from the session cookie
app.get(config.web_context + 'logout', function (req, res) {

    get_logout(req,res);

});


// catch 404 and forward to error handler
app.use(function (req, res, next) {
    var err = new Error('Not Found');
    err.status = 404;
    res.render('error', {
        message: err.message,
        error: err,
        timestamp: req.session.title_timestamp
    });

});


// error handlers

// production error handler
// no stacktraces leaked to user
app.use(function (err, req, res) {
    res.status(err.status || 500);
    res.render('error', {
        timestamp: req.session.title_timestamp,
        message: err.message,
        error: {}
    });
});


/** @export */
module.exports = app;


/** @export */
module.exports.post_contextbroker = post_contextbroker;

/** @export */
module.exports.get_logout = get_logout;

/** @export */
module.exports.get_signin = get_signin;

/** @export */
module.exports.get_login = get_login;

/** @export */
module.exports.check_token = check_token;

/** @export */
module.exports.getOAuthAccessToken_callback = getOAuthAccessToken_callback;

/** @export */
module.exports.oauth_get_callback = oauth_get_callback;