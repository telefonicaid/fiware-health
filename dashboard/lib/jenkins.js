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

var logger = require('./logger'),
    config = require('./config').data,
    jenkins = require('jenkins-api').init(config.jenkins.url);


/**
 * @function regionJobsInProgress
 * Call Jenkins API to identify which sanity check jobs (parametrized by region) are in progress.
 * @param {string} txid
 * @param {function} callback invoked with an object of region_name:in_progress key pairs.
 */
function regionJobsInProgress(txid, callback) {
    var context = {trans: txid, op: 'jenkins#regionJobsInProgress'},
        paramName = config.jenkins.parameterName,
        jobName = config.jenkins.path.split('/').pop(),
        jobProgress = {};

    logger.info(context, 'Checking all jobs "%s" in progress', jobName);

    /* jshint camelcase: false */
    jenkins.job_info(jobName, function (err, job) {
        if (err) {
            callback();
            return logger.error(context, 'Failed to get information for job %s', jobName);
        }
        var buildCount = 0;
        job.builds.forEach(function (build) {
            jenkins.build_info(jobName, build.number, function (err, data) {
                if (err) {
                    logger.error(context, 'Failed to get information for build #%d', build.number);
                } else {
                    var paramActions = data.actions.filter(function (item) {
                    return (item.parameters instanceof Array) || (item instanceof Array);
                    });
                    var parameters = paramActions[0].parameters || paramActions[0],
                        regionName = parameters.filter(function (item) { return item.name === paramName; })[0].value;
                    jobProgress[regionName] = jobProgress[regionName] || data.building;
                }
                if (++buildCount === job.builds.length) {
                    logger.debug(context, 'Progress status=%j', jobProgress);
                    callback(jobProgress);
                }
            });
        });
    });
}


/** @export */
exports.regionJobsInProgress = regionJobsInProgress;
