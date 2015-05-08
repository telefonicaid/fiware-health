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
    logger = require('./logger'),
    dateFormat = require('dateformat'),
    auth = require('http-auth');


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


var basic = auth.basic({
        realm: "Web."
    }, function (username, password, callback) { // Custom authentication method.
        callback(username === "userName" && password === "password");
    }
);

app.use('/refresh', auth.connect(basic), refresh);
app.use('/', index);


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
