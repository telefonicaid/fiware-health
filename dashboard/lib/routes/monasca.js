/*
 * Copyright 2016 Telefónica I+D
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

var config = require('../config').data,
    logger = require('../logger'),
    http = require('http');


/**
 * notify Monasca for a change in region
 * @param {Object} region
 * @param {function} notifyCallback
 */
function notify(region, notifyCallback) {

    var regionName = region.node,
        regionStatus = region.status,
        timestampMillis = region.sanity_check_timestamp;

    logger.info({op: 'monasca#notify'}, 'notify change in region: ' + regionName);
    var payload = {
        "name": "region.sanity_status",
        "dimensions": {
            "unit": "status",
            "resource_id": regionName,
            "source": "fihealth",
            "type": "gauge"
        },
        "timestamp": timestampMillis,
        "value": regionStatus
    };

    var payloadString = JSON.stringify(payload);

    var headers = {
        'Content-Type': 'application/json',
        'Content-Length': payloadString.length,
        'X-Auth-Token': null  // TODO
    };

    var options = {
        host: config.monasca.host,
        port: config.monasca.port,
        path: '/v2.0/metrics',
        method: 'POST',
        headers: headers
    };

    var monascaRequest = http.request(options, function (monascaResponse) {
        monascaResponse.setEncoding('utf-8');
        var responseString = '';

        monascaResponse.on('data', function (data) {
            responseString += data;
        });
        monascaResponse.on('end', function () {
            logger.info('response monasca: region: %s, code: %s, message: %s', regionName, monascaResponse.statusCode,
                monascaResponse.statusMessage);
            notifyCallback();
        });
    });
    monascaRequest.on('error', function (e) {
        logger.error('Error in connection with monasca: ' + e);
        notifyCallback(e);
    });

    monascaRequest.write(payloadString);
    monascaRequest.end();
}


/** @export */
module.exports.notify = notify;
