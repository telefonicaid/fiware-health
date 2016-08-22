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
    logger = require('../logger'),
    http = require('http'),
    config = require('../config').data,
    common = require('./common');

var TEN_SECONDS = 10000;

/**
 *
 * @param {Object} req
 * @param {Object} res
 */
function getRefresh(req, res) {

    var region = req.param('region');

    logger.info({op: 'refresh#get'}, 'refresh region: %s, received role: %s', region, req.session.role);

    if (req.session.role === undefined || req.session.role === '') {
        logger.warn({op: 'refresh#get'}, 'unauthorized operation, invalid role: %s', req.session.role);
        common.notAuthorized(req, res);
        return;
    }

    var payloadString = 'token=' + config.jenkins.token;

    var headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': payloadString.length

    };

    var options = {
        host: config.jenkins.host,
        port: config.jenkins.port,
        path: config.jenkins.path + '/buildWithParameters?' + config.jenkins.parameterName + '=' + region,
        method: 'POST',
        headers: headers
    };

    var jenkinsRequest = http.request(options, function (jenkinsResponse) {
        logger.info('job started');
        jenkinsResponse.setEncoding('utf-8');
        var responseString = '';

        jenkinsResponse.on('data', function (data) {
            responseString += data;
        });
        jenkinsResponse.on('end', function () {
            logger.info('response jenkins: code: %s message: %s',
                jenkinsResponse.statusCode, jenkinsResponse.statusMessage);

            //sleep for 10 seconds
            setTimeout(function () {
                res.redirect(config.webContext);
            }, TEN_SECONDS);
        });
    });
    jenkinsRequest.on('error', function (e) {
        // TODO: handle error.
        logger.error('Error in connection with jenkins: ' + e);

        //sleep for 10 seconds
        setTimeout(function () {
            res.redirect(config.webContext);
        }, TEN_SECONDS);
    });

    jenkinsRequest.write(payloadString);
    jenkinsRequest.end();


}


/* GET refresh. */
router.get('/', getRefresh);

/** @export */
module.exports = router;


/** @export */
module.exports.getRefresh = getRefresh;
