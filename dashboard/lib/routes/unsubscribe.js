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
    http = require('http');


/**
 * router get unSubscribe
 * @param {Object} req
 * @param {Object} res
 */
function getUnSubscribe(req, res) {

    var region = req.param('region');

    var userinfo = req.session.user;

    logger.info({op: 'unsubscribe#get'}, 'unsubscribe to region: ' + region + ' userinfo:' + userinfo);

    var payloadString = 'address=' + userinfo.email;

    var headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': payloadString.length

    };

    var options = {
        host: config.mailman.host,
        port: config.mailman.port,
        path: config.mailman.path + region.toLowerCase(),
        method: 'DELETE',
        headers: headers
    };

    var mailmainRequest = http.request(options, function (mailmanResponse) {
        mailmanResponse.setEncoding('utf-8');
        var responseString = '';

        mailmanResponse.on('data', function (data) {
            responseString += data;
        });
        mailmanResponse.on('end', function () {
            logger.info('response mailman: code: %s message: %s',
                mailmanResponse.statusCode, mailmanResponse.statusMessage);

            res.redirect(config.webContext);
        });
    });
    mailmainRequest.on('error', function (e) {
        logger.error('Error in connection with mailman: ' + e);
        res.redirect(config.webContext);
    });

    mailmainRequest.write(payloadString);
    mailmainRequest.end();


}


/* GET /unsubcribe: send DELETE to mailman*/
router.get('/', getUnSubscribe);

/** @export */
module.exports = router;

/** @export */
module.exports.getUnSubscribe = getUnSubscribe;
