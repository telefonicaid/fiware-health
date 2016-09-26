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

var config = require('./config').data,
    logger = require('./logger'),
    http = require('http'),
    monasca = {};


/**
 * @function withAuthToken
 * Call keystone and invoke callback with the auth token.
 * @param {Object}   context
 * @param {function} callback
 */
monasca.withAuthToken = function (context, callback) {
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
            logger.debug(context, 'Response from Keystone: headers=%j', res.headers);
            logger.info(context, 'Response from Keystone: status=%s', res.statusCode);
            if (res.statusCode === 201) {
                callback(res.headers['x-subject-token']);
            } else {
                callback();
            }
        });
    });

    req.on('error', function (e) {
        var detail = (e.code === 'ECONNRESET') ? 'TIMEOUT' : 'failed';
        logger.error(context, 'Request to Keystone %s: %s', detail, e);
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
 * Notify Monasca for new sanity_status value in a region
 * @param {string} txid
 * @param {Object} region
 * @param {function} notifyCallback
 */
monasca.notify = function (txid, region, notifyCallback) {
    var regionName = region.node,
        context = {trans: txid, op: 'monasca#notify'};

    logger.info(context, 'Notify sanity_status for region "%s"', regionName);
    this.withAuthToken(context, function (authToken) {
        if (!authToken) {
            notifyCallback(new Error('could not get auth token'));
        } else {
            var regionStatus = region.status,
                regionStatusFloat = ['NOK', 'OK', 'POK'].indexOf(regionStatus),
                timestampMillis = new Date(region.timestamp).getTime(),
                elapsedTimeMillis = region.elapsedTimeMillis,
                payload = {
                    'name': 'region.sanity_status',
                    'dimensions': {
                        'region': regionName,
                        'unit': 'status',
                        'resource_id': regionName,
                        'source': 'fihealth',
                        'type': 'gauge'
                    },
                    'timestamp': timestampMillis,
                    'value': regionStatusFloat,
                    'value_meta': {
                        'status': regionStatus,
                        'elapsed_time': elapsedTimeMillis.toString()
                    }
                };

            var payloadString = JSON.stringify(payload);
            logger.debug(context, 'New measurement: %s', payloadString);

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
                    var err = (this.statusCode === 204) ? null : http.STATUS_CODES[this.statusCode];
                    logger.info(context, 'Response from Monasca: region=%s status=%s', regionName, this.statusCode);
                    notifyCallback(err);
                });
            });

            monascaRequest.on('error', function (err) {
                logger.error(context, 'Error in connection with Monasca: %s', err);
                notifyCallback(err);
            });

            monascaRequest.write(payloadString);
            monascaRequest.end();
        }
    });
};


/** Name of notify destination as an attribute */
monasca.notify.destination = 'Monasca';


/** @export */
module.exports = monasca;
