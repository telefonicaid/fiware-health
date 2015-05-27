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
    http = require('http'),
    sleep = require('sleep'),
    config = require('../config').data,
    common=require('./common');


/* GET refresh. */
router.get('/', function (req, res) {

    var region = req.param('region');

    logger.info({op: 'refresh#get'}, 'refresh ' + region + ' received' + ' role: '+req.session.role);

    if (req.session.role==undefined || req.session.role=='') {
        logger.warn({op: 'refresh#get'},'unauthorized operation, invalid role: '+req.session.role);
        common.notAuthorized(req,res);
        return;
    }

    var payload = '';
    var payloadString = 'token='+config.jenkins.token;

    var headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': payloadString.length

    };

    var options = {
        host: config.jenkins.host,
        port: config.jenkins.port,
        path: '/job/FiHealth-SanityCheck-2-Exec-Region/buildWithParameters?OS_REGION_NAME=' + region,
        method: 'POST',
        headers: headers
    };

    var jira_req = http.request(options, function (jenkins_res) {
        logger.info('job started');
        jenkins_res.setEncoding('utf-8');
        var responseString = '';

        jenkins_res.on('data', function (data) {
            responseString += data;
        });
        jenkins_res.on('end', function () {
            logger.info("response jenkins:" + jenkins_res.statusCode + " " + jenkins_res.statusMessage);

            sleep.sleep(10); //sleep for 10 seconds
            res.redirect(config.web_context);
        });
    });
    jira_req.on('error', function (e) {
        // TODO: handle error.
        logger.error('Error in connection with jenkins: ' + e);

        sleep.sleep(10); //sleep for 10 seconds
        res.redirect(config.web_context);
    });

    jira_req.write(payloadString);
    jira_req.end();


});

/** @export */
module.exports = router;
