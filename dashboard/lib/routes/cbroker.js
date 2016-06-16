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
 * Extract regions from the entities included in contextbroker notification
 * @param {string} txid
 * @param {Object} entities
 * @return {Array} with regions parsed
 */
function parseRegions(txid, entities) {
    var context = {trans: txid, op: 'cbroker#parseRegions'};

    logger.debug(context, 'Entities to parse: %j', entities);
    var regions = [];

    entities.contextResponses.forEach(function (entry) {
        var type = entry.contextElement.type;
        if (type === REGION_TYPE) {
            var sanityStatus = '', timestamp = '', elapsedTimeStr = '', elapsedTimeMillis = '', elapsedDate;
            entry.contextElement.attributes.forEach(function (value) {
                var createValue = {};
                createValue[SANITY_STATUS_ATTRIBUTE] = function () {
                    sanityStatus = value.value;
                };
                createValue[TIMESTAMP_ATTRIBUTE] = function () {
                    timestamp = dateFormat(new Date(parseInt(value.value, 10)), 'UTC:yyyy/mm/dd HH:MM Z');
                };
                createValue[ELAPSED_TIME] = function () {
                    elapsedTimeMillis = parseInt(value.value, 10);
                    elapsedDate = new Date(elapsedTimeMillis);
                    elapsedTimeStr = elapsedDate.getUTCHours() + 'h, ' +
                                     elapsedDate.getUTCMinutes() + 'm, ' +
                                     elapsedDate.getUTCSeconds() + 's';
                };

                createValue[value.name]();
            });

            if (config.cbroker.filter.indexOf(entry.contextElement.id) >= 0) {
                logger.warn(context, 'Discarded region "%s" found in filter', entry.contextElement.id);
                global.regionsCache.del(entry.contextElement.id);
            } else {

                var region = global.regionsCache.get(entry.contextElement.id);
                if (region !== undefined) {
                    regions.push(entry.contextElement.id);
                    global.regionsCache.update(entry.contextElement.id, 'status', sanityStatus);
                    global.regionsCache.update(entry.contextElement.id, 'timestamp', timestamp);
                    global.regionsCache.update(entry.contextElement.id, 'elapsedTime', elapsedTimeStr);
                    global.regionsCache.update(entry.contextElement.id, 'elapsedTimeMillis', elapsedTimeMillis);
                } else {
                    logger.warn(context, 'Discarded region "%s" found in context broker', entry.contextElement.id);

                }

            }
        }
    });
    return regions;

}


/**
 * @function retrieveAllRegions
 * Call to context broker and get region status for each region in regionsCache.
 * @param {string} txid
 * @param {function} callback
 */
function retrieveAllRegions(txid, callback) {

    var context = {trans: txid, op: 'retrieveAllRegions'};

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

    logger.debug(context, 'Using configuration: %j', config.cbroker);
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
            logger.debug(context, 'Response string: %s', responseString);
            try {
                var resultObject = JSON.parse(responseString),
                    regions = resultObject.contextResponses.map(function (item) {return item.contextElement.id; });

                logger.info(context, 'Found %d regions: %s', regions.length, regions);
                parseRegions(txid, resultObject);
            } catch (ex) {
                logger.warn(context, 'Error in parse response string: %s %s', responseString, ex);
            }
            callback();
        });
    });

    req.on('error', function (e) {
        if (e.code === 'ECONNRESET') {
            logger.error(context, 'Error in connection by TIMEOUT with context broker: %s', e);
        } else {
            logger.error(context, 'Error in connection with context broker: %s', e);
        }
        callback([]);
    });

    req.setTimeout(config.cbroker.timeout, function () {
        req.abort();
        logger.error(context, 'Timeout in the connection with context broker. Time exceed');
    });

    req.write(payloadString);
    req.end();
}


/**
 * Return the entity involved in a Context Broker notification
 * @param {string} txid
 * @param {*} req
 * @return {Object}
 */
function getEntity(txid, req) {
    var context = {trans: txid, op: 'getEntity'};
    if (typeof req.body !== 'string') {
        logger.warn(context, 'Non-string request body');
        req.body = JSON.stringify(req.body);
    }
    var result = parseRegions(txid, JSON.parse(req.body));
    return global.regionsCache.get(result[0]);

}


/** @export */
module.exports.retrieveAllRegions = retrieveAllRegions;

/** @export */
module.exports.parseRegions = parseRegions;

/** @export */
module.exports.getEntity = getEntity;
