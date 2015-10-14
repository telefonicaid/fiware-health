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

var http = require('http'),
    logger = require('../logger'),
    config = require('../config').data,
    dateFormat = require('dateformat');


var SANITY_STATUS_ATTRIBUTE = 'sanity_status', // field name for value about regions status
    TIMESTAMP_ATTRIBUTE = 'sanity_check_timestamp', // field name for value about timestamp
    ELAPSED_TIME = 'sanity_check_elapsed_time', // field name for value sanity_checks_elapsed_time
    REGION_TYPE = 'region';


/**
 * @function parseRegions
 *
 * @param {Object} entities
 * @return {Array}
 */
function parseRegions(entities) {

    var result = [];

    logger.debug('Entities to parse %j', entities);




    entities.contextResponses.forEach(function (entry) {
        var type = entry.contextElement.type;
        if (type === REGION_TYPE) {
            var sanityStatus = '', timestamp = '', elapsedTime = '';
            entry.contextElement.attributes.forEach(function (value) {
                var createValue = {};
                createValue[SANITY_STATUS_ATTRIBUTE] = function () {
                    sanityStatus = value.value;
                };
                createValue[TIMESTAMP_ATTRIBUTE] = function () {
                    timestamp = dateFormat(new Date(parseInt(value.value)), 'UTC:yyyy/mm/dd HH:MM Z');

                };
                createValue[ELAPSED_TIME] = function () {
                    var myDate = new Date(parseInt(value.value));
                    elapsedTime = myDate.getUTCHours() + 'h, ' + myDate.getUTCMinutes() + 'm, ' +
                                    myDate.getUTCSeconds() + 's';
                };

                createValue[value.name]();
            });
            result.push({node: entry.contextElement.id,
                status: sanityStatus,
                timestamp: timestamp,
                elapsedTime: elapsedTime });
        }
    });


    return result;
}

/**
 * @function retrieveAllRegions
 * Call to context broker and get all regions and status.
 * @param {function} callback
 */
function retrieveAllRegions(callback) {

    var payload = {
        entities: [
            {type: 'region', isPattern: 'true', id: '.*'}
        ],
        attributes: [
            SANITY_STATUS_ATTRIBUTE,
            TIMESTAMP_ATTRIBUTE,
            ELAPSED_TIME
        ]
    };
    var payloadString = JSON.stringify(payload);
    var headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Content-Length': payloadString.length
    };

    logger.debug('Using configuration: %j', config.cbroker);
    var options = {
        host: config.cbroker.host,
        port: config.cbroker.port,
        path: config.cbroker.path,
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
            logger.debug({op: 'retrieveAllRegions'}, 'Response string: %s', responseString);
            try {
                var resultObject = JSON.parse(responseString);
                callback(parseRegions(resultObject));
            } catch (ex) {
                logger.warn({op: 'retrieveAllRegions'}, 'Error in parse response string:  %s %s', responseString, ex);
                callback([]);
            }
        });
    });
    req.on('error', function (e) {
        logger.error('Error in connection with context broker: ' + e);
        callback([]);

    });


    req.write(payloadString);
    req.end();

}

/**
 * invoked when change is received from context broker
 * @param {[]} entities
 */
function changeReceived(entities) {
    logger.debug('entities to parse' + entities);

    var result = parseRegions(entities);
    return result[0];
}


/** @export */
module.exports.retrieveAllRegions = retrieveAllRegions;
/** @export */
module.exports.parseRegions = parseRegions;
/** @export */
module.exports.changeReceived = changeReceived;

