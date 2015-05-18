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
    cbroker = require('./cbroker'),
    domain = require('domain'),
    logger = require('../logger'),
    subscribe = require('./subscribe');


/* GET home page. */
router.get('/', function (req, res) {

    cbroker.retrieveAllRegions(function (regions) {

        logger.info({op: 'index#get'}, 'regions:' + regions);

        var userinfo = req.session.user;

        logger.info({op: 'index#get'}, 'userinfo:' + userinfo);

        if (userinfo != undefined) {

            //search for subscription

            logger.debug({op: 'index#get'}, "regions: " + regions.constructor.name);
            subscribe.searchSubscription(userinfo.email, regions, function () {

                logger.debug("before render: " + JSON.stringify(regions));
                res.render('logged', {name: userinfo.displayName, regions: regions, role: req.session.role});

            });


        }
        else {
            res.render('index', {name: 'sign in', regions: regions, role: req.session.role});

        }
    });

});

/** @export */
module.exports = router;
