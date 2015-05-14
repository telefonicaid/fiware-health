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


var prog = require('../package.json'),
    logger = require('./logger'),
    fs = require('fs'),
    util = require('util'),
    optimist = require('optimist'),
    yamljs = require('yamljs');

/**
 * Program configuration.
 *
 * <var>config</var> attributes will be updated with those read from <var>config_file</var>, if exists,
 * from environment variables and from command line arguments, in that order.
 *
 * @type {{config_file: *, log_level: string}} default configuration file.
 */

var
    config = {
        config_file: util.format(__dirname + '/../config/%s.yml', prog.name),
        log_level: 'DEBUG',
        cbroker: {
            host: '',
            port: '',
            path: '/NGSI10/queryContext'},
        idm: {
            host: 'account.lab.fiware.org',
            clientId: '1181404dd018468a9ab42de26d961c88',
            clientSecret: '/NGSI10/queryContext',
            url: 'https://account.lab.fiware.org',
            callbackURL: 'http://fi-health.lab.fiware.org/login'
        },
        mailman: {
            host: 'localhost',
            port: '8000',
            path: '/',
            email_from: ''
        },
        paths: {
            reports_files: '/var/www/html/RegionSanityCheck',
            reports_url: '/check/report'
        }
    };


// create argument parser
var arg_parser = optimist.demand([])
    .options('h', { 'alias': 'help', 'describe': 'show help message and exit', 'boolean': true })
    .options('v', { 'alias': 'version', 'describe': 'show version and exit', 'boolean': true });

// read configuration file if exists (path maybe taken from command line) and setup logging
arg_parser
    .options('c', { 'alias': 'config-file', 'describe': 'configuration file', 'string': true,
        'default': config.config_file })
    .check(function (argv) {
        config.config_file = argv['config-file'];
    })
    .parse(process.argv);
var cfg_parser_result;
try {
    var cfg_parse = yamljs.parse(fs.readFileSync(config.config_file, 'utf8'));

    cfg_parser_result = [ 'INFO', 'Read configuration file' ];
    ['logging', 'cbroker', 'idm', 'mailman'].forEach(function (key) {
        switch (key in cfg_parse && key) {

            case 'logging':
                config.log_level = cfg_parse.logging.level;
                break;
            case 'cbroker':
                Object.keys(config.cbroker).filter(hasOwnProperty, cfg_parse.cbroker).forEach(function (key) {
                    config.cbroker[key] = cfg_parse.cbroker[key];
                });
                break;
            case 'idm':
                Object.keys(config.idm).filter(hasOwnProperty, cfg_parse.idm).forEach(function (key) {
                    config.idm[key] = cfg_parse.idm[key];
                });
                break;
            case 'mailman':
                Object.keys(config.mailman).filter(hasOwnProperty, cfg_parse.mailman).forEach(function (key) {
                    config.mailman[key] = cfg_parse.mailman[key];
                });
                break;
            default:
                throw new Error(util.format('no "%s" node found', key));


        }
    });
} catch (err) {
    var msg = err.errno ? 'Could not read configuration file' : util.format('Configuration file: %s', err.message);
    cfg_parser_result = [ 'WARN', msg ];
}

// process command line arguments (considering environment variables)
arg_parser
    .usage(util.format('Usage: %s [options]\n\n%s', prog.name, prog.description))
    .options('l', { 'alias': 'log-level', 'describe': 'logging level', 'string': true,
        'default': config.log_level })
    .check(function (argv) {
        if (argv.version) {
            console.error('%s v%s', prog.name, prog.version);
            process.exit(1);
        } else if (argv.help) {
            optimist.showHelp();
            process.exit(0);
        } else Object.keys(argv).forEach(function (key) {
            var attr = key.replace('-', '_');
            if (attr in config) config[attr] = argv[key];

        });

    }
).parse(process.argv);

logger.info("Configuration result:" + cfg_parser_result);


exports.cbroker = config.cbroker;
exports.paths = config.paths;
exports.idm = config.idm;
exports.mailman = config.mailman;
exports.log_level = config.log_level;
