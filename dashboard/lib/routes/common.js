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

var config = require('../config').data;


/**
 * redirect to an error page with 401
 * @param {Object} req
 * @param {Object} res
 */
function notAuthorizedRender(req, res) {
    var err = new Error('Unauthorized');
    err.status = 401;
    res.render('error', {
        message: err.message,
        error: err,
        timestamp: req.session.titleTimestamp
    });
}


function parseRoles(roles) {
    var hasSuperuser = roles.filter(function(obj) {
    return obj.name === 'Superuser';
        });

    var hasAdminUser = roles.filter(function(obj) {
        return obj.name === 'Admin';
    });

    if (hasSuperuser.length > 0) {
        return 'superuser';
    }

    if (hasAdminUser.length > 0) {
        return 'admin';
    }

    return '';
}
/**
 * Convert to lower case and cut the last character
 * @param {string} regionName
 * @returns {string} ready for compare
 */
function getRegionNameForCompare(regionName) {

    return (regionName.substring(0, regionName.length - 1)).toLowerCase();

}
/**
 * Check if region is authorized for an username using list in config file
 * @param {Object} region
 * @param {string} regionName
 * @param {string} username
 */
function checkAuthorizedByConfig(region, regionName, username) {
    if (!region.authorized) {

        var data = config.idm.regionsAuthorized;
        data.filter(function (obj) {
            var key = Object.keys(obj).toString();
            var configRegionName = getRegionNameForCompare(key);
            var configUserName = obj[key];
            if ((configRegionName === regionName) && (configUserName === username)) {
                region.authorized = true;
                return;
            }
        });
    }
}
/**
 * Check if username is authorized to manage region and introduce a new field in object
 * @param {String} username
 */
function addAuthorized(username) {

    global.regionsCache.keys().filter(function (key) {

        var region = global.regionsCache.get(key);
        var regionName = getRegionNameForCompare(region.node);
        region.authorized = ((username.indexOf(regionName)) !== -1);

        checkAuthorizedByConfig(region, regionName, username);
        global.regionsCache.update(region.node, 'authorized', region.authorized);

    });

}



/** @export */
module.exports.notAuthorized = notAuthorizedRender;

/** @export */
module.exports.parseRoles = parseRoles;


/** @export */
module.exports.addAuthorized = addAuthorized;
