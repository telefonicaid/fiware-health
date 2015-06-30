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
    router = express.Router(),
    dateFormat = require('dateformat'),
    config = require('../config').data,
    domain = require('domain'),
    logger = require('../logger'),
    http = require('http'),
    sleep = require('sleep'),
    _ = require('underscore');


/* GET /subcribe: send PUT to mailman*/
router.get('/', getSubscribe);

/**
 * router get subscribe
 * @param {Object} req
 * @param {Object} res
 */
function getSubscribe(req, res) {

    var region = req.param('region');

    var userinfo = req.session.user;

    logger.info({op: 'subscribe#get'}, 'subscribe to region: ' + region + ' userinfo:' + userinfo);

    var payloadString = 'address=' + userinfo.email;

    var headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': payloadString.length

    };

    var options = {
        host: config.mailman.host,
        port: config.mailman.port,
        path: config.mailman.path + region.toLowerCase(),
        method: 'PUT',
        headers: headers
    };

    var mailmain_req = http.request(options, function (mailman_res) {
        mailman_res.setEncoding('utf-8');
        var responseString = '';

        mailman_res.on('data', function (data) {
            responseString += data;
        });
        mailman_res.on('end', function () {
            logger.info('response mailman: region (' + region.node + ') ' + mailman_res.statusCode + ' ' + responseString);

            res.redirect(config.web_context);
        });
    });
    mailmain_req.on('error', function (e) {
        logger.error('Error in connection with mailman: ' + e);
        res.redirect(config.web_context);
    });

    mailmain_req.write(payloadString);
    mailmain_req.end();

}

/**
 *
 * @param {Object} user
 * @param {[]} regions
 * @param {callback} callback
 */
function searchSubscription(user, regions, callback) {

    logger.debug('searchSubscription');
    var finished = _.after(regions.length, callback);
    regions.map(function (region) {


        isSubscribed(user, region, finished);

    });
}

/**
 * Connect to mailman and check if user is subscribed to region list
 * @param {Object} user
 * @param {String} region
 * @param {function} isSubscribed_callback
 */
function isSubscribed(user, region, isSubscribed_callback) {

    var options = {
        host: config.mailman.host,
        port: config.mailman.port,
        path: config.mailman.path + region.node.toLowerCase(),
        method: 'GET'
    };


    function isMail(value) {
        return value == user;
    }

    var mailmain_req = http.request(options, function (mailman_res) {
        mailman_res.setEncoding('utf-8');
        var responseString = '';

        mailman_res.on('data', function (data) {
            responseString += data;
        });
        mailman_res.on('end', function () {
            logger.info('response mailman: region (' + region.node + ') ' + mailman_res.statusCode + ' ' + responseString);
            try {
                var array = JSON.parse(responseString);
                logger.debug('all users:' + array);
                var new_array = array.filter(isMail);
                logger.debug('new_array:' + new_array);
                region.subscribed = new_array.length == 1;
            } catch (ex) {
                region.subscribed = false;
            }
            isSubscribed_callback();


        });
    });
    mailmain_req.on('error', function (e) {
        logger.error({op: 'subscribe#isSubscribed'},'Error in connection with mailman: ' + e);
        region.subscribed = false;
        isSubscribed_callback();
    });

    mailmain_req.end();
}

/**
 * notify to region list for a change in region
 * @param {String} region
 * @param {function} notify_callback
 */
function notify(region, notify_callback) {

    logger.info({op: 'subscribe#notify'}, 'notify to region: ' + region);


    var payloadString = 'name_from= fi-health sanity&';
        payloadString += 'email_from=' + config.mailman.email_from + '&';
        payloadString += 'subject=Status changed for region ' + region + '&';
        payloadString += 'body=Status changed for region ' + region;

    var headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': payloadString.length

    };

    var options = {
        host: config.mailman.host,
        port: config.mailman.port,
        path: config.mailman.path + region.toLowerCase() + '/sendmail',
        method: 'POST',
        headers: headers
    };


    var mailmain_req = http.request(options, function (mailman_res) {
        mailman_res.setEncoding('utf-8');
        var responseString = '';

        mailman_res.on('data', function (data) {
            responseString += data;
        });
        mailman_res.on('end', function () {
            logger.info('response mailman: region: %s, code: %s, message: %s', region, mailman_res.statusCode,
                mailman_res.statusMessage);
            notify_callback();

        });
    });
    mailmain_req.on('error', function (e) {
        logger.error('Error in connection with mailman: ' + e);
    });

    mailmain_req.write(payloadString);
    mailmain_req.end();
}


/** @export */
module.exports = router;

/** @export */
module.exports.getSubscribe = getSubscribe;
/** @export */
module.exports.isSubscribed = isSubscribed;
/** @export */
module.exports.searchSubscription = searchSubscription;
/** @export */
module.exports.notify = notify;

