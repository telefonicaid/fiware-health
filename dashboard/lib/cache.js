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

var NodeCache = require('node-cache');

var regionsCache = new NodeCache({ stdTTL: 0, checkperiod: 600 });


/**
 * Load regions from settings and assign default values
 * @param {string} file name
 */
regionsCache.init = function (settings) {
    /**
     * Read settings file with available regions
     */

    try {
        var json = JSON.parse(require('fs').readFileSync(settings, 'utf8'));

        /*jshint -W069 */
        for (var region in json['region_configuration']) {

            regionsCache.set(region, {
                node: region,
                status: '',
                timestamp: 0,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            });
        }

    } catch (err) {
        console.log('warning, fail reading settings file: ' + settings);
    }


};

/**
 * Compare two region name nodes
 * @param {String} a
 * @param {String} b
 * @returns {number}
 */
function compare(a, b) {
    if (a > b) {
        return 1;
    }
    if (a < b) {
        return -1;
    }
    // a must be equal to b
    return 0;
}

/**
 * return a dict with regions and regions object by asc order
 * @returns {Array}
 */
regionsCache.list = function() {

    var regionNames = regionsCache.keys();
    var regions = [];

    regionNames.sort(compare);

    regionNames.forEach(function (key) {
        regions.push(regionsCache.get(key));
    });

    return regions;
};

/**
 * udpate or add new value to region
 * @param {String} region name
 * @param {String} name of field to set, (i.g: status, timestamp)
 * @param {Object} the new value
 */
regionsCache.update = function (regionName, field, value) {

    var region = regionsCache.get(regionName);
    region[field] = value;
    regionsCache.set(regionName, region);

};


/** @export */
module.exports = regionsCache;

/** @export */
module.exports.compare = compare;
