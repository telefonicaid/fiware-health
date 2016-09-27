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
    config = require('../config').data,
    logger = require('../logger'),
    http = require('http'),
    _ = require('underscore');


/**
 * Called by router when GET
 * @param {Object} req
 * @param {Object} res
 */
function getSubscribe(req, res) {

    var region = req.param('region');

    var userinfo = req.session.user;

    logger.info({op: 'subscribe#get'}, 'Subscribe to region: %s userinfo: %s', region, userinfo);

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

    var mailmainRequest = http.request(options, function (mailmanResponse) {
        mailmanResponse.setEncoding('utf-8');
        var responseString = '';

        mailmanResponse.on('data', function (data) {
            responseString += data;
        });
        mailmanResponse.on('end', function () {
            logger.info('response mailman: region (' + region.node +
                ') ' + mailmanResponse.statusCode + ' ' + responseString);

            res.redirect(config.webContext);
        });
    });
    mailmainRequest.on('error', function (e) {
        logger.error('Error in connection with mailman: %s', e);
        res.redirect(config.webContext);
    });

    mailmainRequest.write(payloadString);
    mailmainRequest.end();

}

/**
 * Connect to mailman and check if user is subscribed to region list
 * @param {Object} user
 * @param {String} region
 * @param {function} isSubscribedCallback
 */
function isSubscribed(user, region, isSubscribedCallback) {

    var options = {
        host: config.mailman.host,
        port: config.mailman.port,
        path: config.mailman.path + region.node.toLowerCase(),
        method: 'GET'
    };

    function isMail(value) {
        return value === user;
    }

    var mailmainRequest = http.request(options, function (mailmanResponse) {
        mailmanResponse.setEncoding('utf-8');
        var responseString = '';

        mailmanResponse.on('data', function (data) {
            responseString += data;
        });
        mailmanResponse.on('end', function () {
            logger.info('response mailman: region (' + region.node +
                ') ' + mailmanResponse.statusCode + ' ' + responseString);
            try {
                var array = JSON.parse(responseString);
                logger.debug('all users:' + array);
                var newArray = array.filter(isMail);
                logger.debug('new_array:' + newArray);
                region.subscribed = newArray.length === 1;
            } catch (ex) {
                region.subscribed = false;
            }
            config.regions.update(region.node, 'subscribed', region.subscribed);
            isSubscribedCallback();


        });
    });

    mailmainRequest.on('error', function (e) {
        logger.error({op: 'subscribe#isSubscribed'}, 'Error in connection with mailman: %s', e);
        region.subscribed = false;
        config.regions.update(region.node, 'subscribed', region.subscribed);
        isSubscribedCallback();
    });

    mailmainRequest.end();
}


/** Find if user has subcriptions to regions
 * @param {Object} user
 * @param {callback} callback
 */
function searchSubscription(user, callback) {

    logger.debug('searchSubscription');
    var regions = config.regions.list();
    var finished = _.after(regions.length, callback);
    regions.map(function (region) {
        isSubscribed(user, region, finished);
    });
}


/**
 * notify mailing list for a change in region
 * @param {string} txid
 * @param {Object} region
 * @param {function} notifyCallback
 */
function notify(txid, region, notifyCallback) {

    var regionName = region.node,
        regionStatus = region.status,
        context = {trans: txid, op: 'subscribe#notify'};

    logger.info(context, 'notify change in region "%s"', regionName);

    var payloadString = 'name_from= fi-health sanity&';
    payloadString += 'email_from=' + config.mailman.emailFrom + '&';
    payloadString += 'subject=Status changed for region ' + regionName + '&';
    payloadString += 'body=Status changed to ' + regionStatus + ' for region ' + regionName +
                         ' (visit ' + config.fiHealthUrl + 'report/' + regionName + '_results.html for details)';

    var headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': payloadString.length

    };

    var options = {
        host: config.mailman.host,
        port: config.mailman.port,
        path: config.mailman.path + regionName.toLowerCase() + '/sendmail',
        method: 'POST',
        headers: headers
    };

    var mailmanRequest = http.request(options, function (mailmanResponse) {
        mailmanResponse.setEncoding('utf-8');
        var responseString = '';

        mailmanResponse.on('data', function (data) {
            responseString += data;
        });
        mailmanResponse.on('end', function () {
            logger.info(context, 'response mailman: region: %s, code: %s, message: %s', regionName,
                mailmanResponse.statusCode, mailmanResponse.statusMessage);
            notifyCallback();
        });
    });

    mailmanRequest.on('error', function (e) {
        logger.error(context, 'Error in connection with mailman: %s', e);
        notifyCallback(e);
    });

    mailmanRequest.write(payloadString);
    mailmanRequest.end();
}


/** Name of notify destination as an attribute */
notify.destination = 'mailing list';


router.get('/', getSubscribe);

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

