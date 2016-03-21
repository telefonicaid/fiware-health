/*
 * Copyright 2016 Telefónica I+D
 * All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the 'License'); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
'use strict';
/* jshint camelcase: false */


var config = require('./config').data,
    logger = require('./logger'),
    http = require('http'),
    monasca = {};


/**
 * @function withAuthToken
 * Call keystone and invoke callback with the auth token.
 * @param {function} callback
 */
monasca.withAuthToken = function (callback) {
    var payload = {
        auth: {
            identity: {
                methods: [
                    'password'
                ],
                password: {
                    user: {
                        domain: {
                            id: 'default'
                        },
                        name: config.monasca.keystoneUser,
                        password: config.monasca.keystonePass
                    }
                }
            }
        }
    };

    var payloadString = JSON.stringify(payload);
    var contentType = 'application/json';
    var headers = {
        'Content-Length': payloadString.length,
        'Content-Type': contentType,
        'Accept': contentType
    };
    var options = {
        host: config.monasca.keystoneHost,
        port: config.monasca.keystonePort,
        path: config.monasca.keystonePath,
        method: 'POST',
        headers: headers
    };

    var req = http.request(options, function (res) {
        res.setEncoding('utf-8');
        var responseString = '';

        res.on('data', function (data) {
            responseString += data;
        });
        res.on('end', function () {
            logger.debug('Response from Keystone: %s headers=%s', responseString, res.headers);
            logger.info('Response from Keystone: status=%s', res.statusCode);
            if (res.statusCode === 201) {
                callback(res.headers['x-subject-token']);
            } else {
                callback();
            }
        });
    });

    req.on('error', function (e) {
        var detail = (e.code === 'ECONNRESET') ? 'TIMEOUT' : 'failed';
        logger.error('Request to Keystone %s: %s', detail, e);
        callback();
    });

    req.setTimeout(10000, function () {
        req.abort();
    });

    req.write(payloadString);
    req.end();
};


/**
 * @function notify
 * Notify Monasca for a change in region
 * @param {Object} region
 * @param {function} notifyCallback
 */
monasca.notify = function (region, notifyCallback) {
    var regionName = region.node;
    logger.info({op: 'monasca#notify'}, 'notify change in region %s', regionName);
    this.withAuthToken(function (authToken) {
        if (!authToken) {
            notifyCallback(new Error('could not get auth token'));
        } else {
            var regionStatus = region.status,
                timestampMillis = new Date(region.timestamp).getTime(),
                elapsedTimeMillis = region.elapsedTimeMillis,
                payload = {
                    'name': 'region.sanity_status',
                    'dimensions': {
                        'unit': 'status',
                        'resource_id': regionName,
                        'source': 'fihealth',
                        'type': 'gauge'
                    },
                    'timestamp': timestampMillis,
                    'value': ['NOK', 'OK', 'POK'].indexOf(regionStatus),
                    'value_meta': {
                        'status': regionStatus,
                        'elapsed_time': elapsedTimeMillis.toString()
                    }
                };
            var payloadString = JSON.stringify(payload);
            var headers = {
                'Content-Type': 'application/json',
                'Content-Length': payloadString.length,
                'X-Auth-Token': authToken
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
                    logger.info('response monasca: region: %s, code: %s, message: %s',
                                regionName, monascaResponse.statusCode, monascaResponse.statusMessage);
                    notifyCallback();
                });
            });
            monascaRequest.on('error', function (e) {
                logger.error('Error in connection with monasca: %s', e);
                notifyCallback(e);
            });

            monascaRequest.write(payloadString);
            monascaRequest.end();
        }
    });
};


/** @export */
module.exports = monasca;
