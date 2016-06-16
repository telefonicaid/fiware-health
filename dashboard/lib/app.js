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
    cuid = require('cuid'),
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
    OAuth2 = require('./oauth2').OAuth2,
    constants = require('./constants'),
    monasca = require('./monasca'),
    NodeCache = require('node-cache');


global.regionsCache = new NodeCache({ stdTTL: 0, checkperiod: 600 });

/**
 * Compare two region name nodes
 * @param {Json} a
 * @param {Json} b
 * @returns {number}
 */
function compare(a, b) {
    if (a > b) {
        return 1;
    }
    if (a < b) {
        return -1;
    }
    // a must be equal to b
    return 0;
}

/**
 * getRegions return a dict with regions and regions object by asc order
 * @returns {Array}
 */
global.regionsCache.getRegions = function () {

    var regionNames = global.regionsCache.keys();
    var regions = [];

    regionNames.sort(compare);

    regionNames.forEach(function (key) {
        regions.push(global.regionsCache.get(key));
    });

    return regions;
};

global.regionsCache.update = function (regionName, field, value) {

    var region = global.regionsCache.get(regionName);
    region[field] = value;
    global.regionsCache.set(regionName, region);

};

var app = express();



logger.info('Running app in web context: %s', config.webContext);


/**
 * Base web context in URL
 * @type {string}
 */
app.base = config.webContext;



/**
 * Web context
 * @type {string}
 */
app.locals.webContext = config.webContext;


/**
 * Title of web page
 * @type {string}
 */
app.locals.title = 'Sanity check status';


/**
 * Compile Stylus CSS on runtime
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


function loadRegionsFromSettings() {
    /**
     * Read settings file with available regions
     */

    var json = JSON.parse(require('fs').readFileSync('config/settings.json', 'utf8'));


    var regions = [];
    for (region in json.region_configuration) {
        regions.push(region);
    }

    /**
     * Open and configure cache
     */

    for (var region in json.region_configuration) {

        regionsCache.set(region, {
            node: region,
            status: '',
            timestamp: 0,
            elapsedTime: 'NaNh, NaNm, NaNs',
            elapsedTimeMillis: NaN
        });
    }


}


/**
 * Called when POST on either `CONTEXT_SANITY_STATUS_VALUE` or `CONTEXT_SANITY_STATUS_CHANGE`
 * @param {*} req
 * @param {*} res
 */
function postContextBroker(req, res) {

    var txid = req.headers[constants.TRANSACTION_ID_HEADER.toLowerCase()] || cuid(),
        context = {trans: txid, op: 'app#contextbroker'},
        mailman = subscribe;

    try {
        var region = cbroker.getEntity(txid, req),
            notifyExclude = [ constants.GLOBAL_STATUS_OTHER ];

        logger.info(context, 'Received sanity_status notification from Context Broker for region "%s"', region.node);
        res.status(200).end();

        if (notifyExclude.indexOf(region.status) === -1) {
            var recipient = (req.path.match('/' + constants.CONTEXT_SANITY_STATUS_CHANGE + '$')) ? mailman : monasca;
            recipient.notify(region, function (err) {
                if (err) {
                    logger.error(context, 'Notification to %s failed: %s', recipient.notify.destination, err);
                } else {
                    logger.info(context, 'Notification to %s succeeded', recipient.notify.destination);
                }
            });
        } else {
            logger.info(context, 'Discarded sanity_status notification (status %s is excluded)', region.status);
        }

    } catch (ex) {
        logger.error(context, 'Processing of Context Broker notification failed: %s', ex);
        res.status(400).send({ error: 'bad request! ' + ex });
    }

}


/**
 * Called when GET on `CONTEXT_LOGOUT`
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
 * Called when GET on `CONTEXT_SIGNIN`
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
 * Check access token
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


loadRegionsFromSettings()

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

// trace all requests and include transaction id (if not present)
app.use(function (req, res, next) {
    var txidHeader = constants.TRANSACTION_ID_HEADER.toLowerCase(),
        txid = req.headers[txidHeader] || cuid(),
        context = {trans: txid, op: 'app#use'};
    logger.debug(context, '%s %s', req.method, req.url);
    req.headers[txidHeader] = txid;
    next();
});


app.use(config.paths.reportsUrl, express.static(config.paths.reportsFiles));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(config.webContext, express.static(path.join(__dirname, 'public')));


app.use(config.webContext + constants.CONTEXT_REFRESH, function (req, res, next) {
    checkToken(req, res, next, 'Accessing to /' + constants.CONTEXT_REFRESH);
}, refresh);


app.use(config.webContext + constants.CONTEXT_SUBSCRIBE, function (req, res, next) {
    checkToken(req, res, next, 'Accessing to /' + constants.CONTEXT_SUBSCRIBE);
}, subscribe);


app.use(config.webContext + constants.CONTEXT_UNSUBSCRIBE, function (req, res, next) {
    checkToken(req, res, next, 'Accessing to /' + constants.CONTEXT_UNSUBSCRIBE);
}, unsubscribe);


app.use(config.webContext, index);


// Creates oauth library object with the config data
var oa = new OAuth2(config.idm.clientId,
    config.idm.clientSecret,
    config.idm.url,
    '/oauth2/authorize',
    '/oauth2/token',
    config.idm.callbackURL);


app.get(config.webContext + constants.CONTEXT_SIGNIN, function (req, res) {
    getSignin(req, res, oa);
});


app.get(config.webContext + constants.CONTEXT_LOGIN, function (req, res) {
    getLogin(req, res, oa);
});


// Change sanity_status notifications from Context Broker
app.post(config.webContext + constants.CONTEXT_SANITY_STATUS_CHANGE, function (req, res) {
    postContextBroker(req, res);
});


// Value sanity_status notifications from Context Broker
app.post(config.webContext + constants.CONTEXT_SANITY_STATUS_VALUE, function (req, res) {
    postContextBroker(req, res);
});


// Redirection to IDM authentication portal
app.get(config.webContext + constants.CONTEXT_AUTH, function (req, res) {
    var path = oa.getAuthorizeUrl();
    res.redirect(path);
});


// Handles logout requests to remove accessToken from the session cookie
app.get(config.webContext + constants.CONTEXT_LOGOUT, function (req, res) {
    getLogout(req, res);
});


// Catch 404 and forward to error handler
app.use(function (req, res) {
    var err = new Error('Not Found');
    err.status = 404;
    res.render('error', {
        message: err.message,
        error: err,
        timestamp: req.session.titleTimestamp
    });
});


// Error handlers
// Production error handler (no stacktraces leaked to user)
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

module.exports.regionsCache = regionsCache;

/** @export */
module.exports.postContextBroker = postContextBroker;

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

/** @export */
module.exports.compare = compare;

