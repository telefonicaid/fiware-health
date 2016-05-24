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

var cuid = require('cuid'),
    express = require('express'),
    router = express.Router(),
    subscribe = require('./subscribe'),
    cbroker = require('./cbroker'),
    constants = require('../constants'),
    jenkins = require('../jenkins'),
    logger = require('../logger'),
    config = require('../config').data,
    common = require('./common');


var MESSAGE = 'Page cannot be displayed due to a Context Broker error (connection timed out or service was down).';


/**
 * Compare two region name nodes
 * @param {Json} a
 * @param {Json} b
 * @returns {number}
 */
function compare(a, b) {
    if (a.node > b.node) {
        return 1;
    }
    if (a.node < b.node) {
        return -1;
    }
    // a must be equal to b
    return 0;
}


/**
 * @param {*} req
 * @param {*} res
 */
function getIndex(req, res) {

    var txid = req.headers[constants.TRANSACTION_ID_HEADER.toLowerCase()] || cuid(),
        context = {trans: txid, op: 'index#get'};

    /**
     * callback for cbroker.retrieveAllRegions
     * @param {[]} regions
     */
    function callbackRetrieveRegions(regions) {

        logger.debug(context, 'Response from Context Broker: %j', regions);

        var userinfo = req.session.user;

        logger.debug(context, 'User role: %s info: %j', req.session.role, userinfo);

        regions.sort(compare);

        if (userinfo !== undefined) {
            //search for subscription

            logger.debug(context, 'Regions: %s', regions.constructor.name);

            if (regions.length === 0) {
                res.render('error', {
                    name: userinfo.displayName,
                    role: req.session.role,
                    message: MESSAGE,
                    logoutUrl: config.idm.logoutURL,
                    error: {
                        status: '',
                        message: 'cb timeout'
                    }
                });
                return;
            }

            var afterSearchCallback = function () {
                regions = common.addAuthorized(regions, userinfo.displayName);
                logger.debug(context, 'Before render: %s', JSON.stringify(regions));
                res.render('logged', {
                    name: userinfo.displayName,
                    regions: regions,
                    role: req.session.role,
                    logoutUrl: config.idm.logoutURL
                });
            };

            subscribe.searchSubscription(userinfo.email, regions, afterSearchCallback);

        } else {

            if (regions.length === 0) {
                res.render('error', {
                    name: 'sign in',
                    role: req.session.role,
                    logoutUrl: config.idm.logoutURL,
                    message: MESSAGE,
                    error: {
                        status: '',
                        message: 'cb timeout'
                    }
                });
                return;
            }

            res.render('index', {
                name: 'sign in',
                regions: regions,
                role: req.session.role,
                logoutUrl: config.idm.logoutURL
            });

        }
    }

    logger.info(context, 'Request for Sanity Check Status main page');

    cbroker.retrieveAllRegions(txid, function (regions) {
        // Update region sanity_status to `GLOBAL_STATUS_OTHER` for those currently in progress
        jenkins.regionJobsInProgress(txid, function (progress) {
            if (progress) {
                regions.forEach(function (region) {
                    if (progress[region.node] === true) {
                        region.status = constants.GLOBAL_STATUS_OTHER;
                    }
                });
            }
            callbackRetrieveRegions(regions);
        });
    });
}


/* GET home page. */
router.get('/', getIndex);


/** @export */
module.exports = router;

/** @export */
module.exports.getIndex = getIndex;

/** @export */
module.exports.compare = compare;
