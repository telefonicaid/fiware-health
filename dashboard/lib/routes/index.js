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
 * @param {*} req
 * @param {*} res
 */
function getIndex(req, res) {

    var txid = req.headers[constants.TRANSACTION_ID_HEADER.toLowerCase()] || cuid(),
        context = {trans: txid, op: 'index#get'};

    /**
     * callback for cbroker.retrieveAllRegions
     */
    function callbackRetrieveRegions() {

        var regions = config.regions.getRegions();
        logger.debug(context, 'Response from Context Broker: %j', regions);

        var userinfo = req.session.user;

        logger.debug(context, 'User role: %s info: %j', req.session.role, userinfo);


        if (userinfo !== undefined) {
            //search for subscription

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
                common.addAuthorized(userinfo.displayName);
                regions = config.regions.getRegions();
                logger.debug(context, 'Before render: %s', JSON.stringify(regions));
                res.render('logged', {
                    name: userinfo.displayName,
                    regions: regions,
                    role: req.session.role,
                    logoutUrl: config.idm.logoutURL
                });
            };

            subscribe.searchSubscription(userinfo.email, afterSearchCallback);

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

    cbroker.retrieveAllRegions(txid, function () {
        // Update region sanity_status to `GLOBAL_STATUS_OTHER` for those currently in progress
        jenkins.regionJobsInProgress(txid, function (progress) {
            if (progress) {
                config.regions.keys.forEach(function (region) {
                    if (progress[region] === true) {
                        config.regions.update(region, 'status', constants.GLOBAL_STATUS_OTHER);
                    }
                });
            }
            callbackRetrieveRegions();
        });
    });
}


/* GET home page. */
router.get('/', getIndex);


/** @export */
module.exports = router;

/** @export */
module.exports.getIndex = getIndex;

