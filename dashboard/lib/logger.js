/*
 * Copyright 2013 Telefónica I+D
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


/**
 * Module for logging.
 *
 * @module logger
 */


var util = require('util'),
    domain = require('domain'),
    logger = require('logops');


/**
 * Get the context for a trace.
 *
 * @return {Object} The context object.
 */
logger.getContext = function () {
    return (domain.active) ? domain.active.context : {};
};


/**
 * Return a String representation for a trace.
 *
 * @param {String} level    One of the valid logging levels.
 * @param {Object} context  Additional information to add to the trace.
 * @param {String} message  The main message to be added to the trace.
 * @param {Array}  args     More arguments provided to the log function.
 *
 * @return {String} The formatted trace.
 */
logger.format = (process.env.NODE_ENV === 'development') ?
    logger.format :
    function (level, context, message, args) {
        args.unshift(
            'time=%s | lvl=%s | trans=%s | op=%s | msg=' + message,
            (new Date()).toISOString(),
            level,
            context.trans || 'n/a',
            context.op || 'n/a'
        );
        return util.format.apply(global, args);
    };


/**
 * Logger object.
 */
module.exports = logger;
