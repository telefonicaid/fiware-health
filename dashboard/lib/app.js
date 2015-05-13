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
// TODO var favicon = require('serve-favicon');
    cookieParser = require('cookie-parser'),
    bodyParser = require('body-parser'),
    index = require('./routes/index'),
    refresh = require('./routes/refresh'),
    subscribe = require('./routes/subscribe'),
    unsubscribe = require('./routes/unsubscribe'),
    logger = require('./logger'),
    dateFormat = require('dateformat'),
    OAuth2 = require('./oauth2').OAuth2,
    config = require('./config');


var app = express();

/**
 * compile stylus css on runtime
 * @param str
 * @param path
 * @return {*|Function}
 */
function compile(str, path) {
    return stylus(str)
        .set('filename', path)
        .use(nib());
}


// view engine setup
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

// uncomment after placing your favicon in /public
//app.use(favicon(__dirname + '/public/favicon.ico'));

app.use(stylus.middleware(
    { src: __dirname + '/public', compile: compile
    }
));

app.use(session({secret: 'ssshhhhh', title_timestamp: ''}));

// trace all requests
app.use(function (req, res, next) {
    logger.debug('%s %s %s', req.method, req.url, req.path);

    next();
});


app.use("/report", express.static('/var/www/html/RegionSanityCheckv2/'));
app.use("/RegionSanityCheck", express.static('/var/www/html/RegionSanityCheck/'));

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));


app.use('/refresh', function (req, res, next) {
    logger.debug('Accessing to relaunch');
    if (req.session.access_token) {

        next(); // pass control to the next handler
    } else {
        res.redirect('/error');
    }
}, subscribe);

app.use('/subscribe', function (req, res, next) {
    logger.debug('Accessing to subscribe');
    if (req.session.access_token) {

        next(); // pass control to the next handler
    } else {
        res.redirect('/error');
    }
}, subscribe);

app.use('/unsubscribe', function (req, res, next) {
    logger.debug('Accessing to unSubscribe');
    if (req.session.access_token) {

        next(); // pass control to the next handler
    } else {
        res.redirect('/error');
    }
}, unsubscribe);


app.use('/', index);

//configure login with oAuth

// Creates oauth library object with the config data
var oa = new OAuth2(config.idm.clientId,
    config.idm.clientSecret,
    config.idm.url,
    '/oauth2/authorize',
    '/oauth2/token',
    config.idm.callbackURL);


// Handles requests to the main page
app.get('/signin', function (req, res) {
    logger.debug({op: 'app#get signin'}, "token: " + req.session.access_token);

    // If auth_token is not stored in a session redirect to IDM
    if (!req.session.access_token) {
        var path = oa.getAuthorizeUrl();
        logger.debug({op: 'app#get signin'}, "idm path: " + path);
        res.redirect(path);
        // If auth_token is stored in a session cookie it sends a button to get user info
    } else {

        oa.get('https://account.lab.fiware.org/user/', req.session.access_token, function (e, response) {
            logger.debug("userinfo: " + response);
            if (response != undefined) {
                var user = JSON.parse(response);
                req.session.user = user;
            }
            res.redirect('/');

        });

    }
});

// Handles requests from IDM with the access code
app.get('/login', function (req, res) {

    logger.debug({op: 'app#get login'}, "req:" + req.query.code);

    // Using the access code goes again to the IDM to obtain the access_token
    oa.getOAuthAccessToken(req.query.code, function (e, results) {
        logger.debug({op: 'app#get login'}, "get access token:" + results);

        if (results != undefined) {

            // Stores the access_token in a session cookie
            req.session.access_token = results.access_token;

            logger.debug({op: 'app#get login'}, "access_token: " + results.access_token);

            oa.get('https://account.lab.fiware.org/user/', results.access_token, function (e, response) {
                logger.debug({op: 'app#get login'}, "response get userinfo: " + response);
                if (response != undefined) {
                    var user = JSON.parse(response);
                    req.session.user = user;
                } else {
                    req.session.access_token = undefined;
                    req.session.user = undefined;
                }
                res.redirect('/');

            });
        } else {
            res.redirect('/');

        }


    });


})
;

// Redirection to IDM authentication portal
app.get('/auth', function (req, res) {
    var path = oa.getAuthorizeUrl();
    res.redirect(path);
});

// Handles logout requests to remove access_token from the session cookie
app.get('/logout', function (req, res) {

    req.session.access_token = undefined;
    req.session.user = undefined;
    res.redirect('/');
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

    //next(err);
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
