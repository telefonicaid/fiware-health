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
    http = require('http');

/* GET refresh. */
router.get('/', function (req, res) {

    var region = req.param('region');

    logger.info({op: 'refresh#get'}, 'refresh ' + region + ' received');
    // http://fi-health.lab.fi-ware.eu:8080/login?from=%2Fjob%2FFiHealth-SanityCheck-2-Exec-Region%2FbuildWithParameters%3FOS_REGION_NAME%3DSpain%2520--data%2520token%3DFIHEALTH_TOKEN_123456
    var payload = '';
    var payloadString = 'token=FIHEALTH_TOKEN_123456';

    var headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': payloadString.length

    };

    var options = {
        host: 'fi-health.lab.fiware.org',
        port: 8080,
        path: '/job/FiHealth-SanityCheck-2-Exec-Region/buildWithParameters?OS_REGION_NAME=' + region,
        method: 'POST',
        headers: headers
    };

    var jira_req = http.request(options, function (res) {
        logger.info('job started');
        res.setEncoding('utf-8');
        var responseString = '';

        res.on('data', function (data) {
            responseString += data;
        });
        res.on('end', function () {
            logger.info("response jenkins:" + res.statusCode + " " + res.statusMessage);
        });
    });
    jira_req.on('error', function (e) {
        // TODO: handle error.
        logger.error('Error in connection with jenkins: ' + e);
    });

    jira_req.write(payloadString);
    jira_req.end();
    res.redirect('/');

});

/** @export */
module.exports = router;
