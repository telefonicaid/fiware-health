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
    cbroker = require('./cbroker'),
    logger = require('../logger'),
    subscribe = require('./subscribe'),
    config = require('../config').data,
    common = require('./common');



/**
 *
 * @param {*} req
 * @param {*} res
 */
function getIndex (req, res) {

    /**
     * callback for cbroker.retrieveAllRegions
     * @param {[]} regions
     */
    function callbackRetrieveRegions(regions) {

        logger.info({op: 'index#get'}, 'Regions: %j', regions);

        var userinfo = req.session.user;

        logger.info({op: 'index#get'}, 'User info: %j', userinfo);

        if (userinfo !== undefined) {

            //search for subscription

            logger.debug({op: 'index#get'}, 'Regions: %s', regions.constructor.name);

            var afterSearchCallback = function () {

                regions = common.addAuthorized(regions, userinfo.displayName);

                logger.debug('before render: %s', JSON.stringify(regions));
                console.log({name: userinfo.displayName, regions: regions, role: req.session.role});
                res.render('logged', {name: userinfo.displayName, regions: regions, role: req.session.role,
                    logoutUrl: config.idm.logoutURL});

            };

            subscribe.searchSubscription(userinfo.email, regions, afterSearchCallback);


        }
        else {
            res.render('index', {name: 'sign in', regions: regions, role: req.session.role,
                logoutUrl: config.idm.logoutURL});

        }
    }

    cbroker.retrieveAllRegions(callbackRetrieveRegions);

}


/* GET home page. */
router.get('/', getIndex);

/** @export */
module.exports = router;

/** @export */
module.exports.getIndex = getIndex;


