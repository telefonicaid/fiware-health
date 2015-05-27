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

var path = require('path'),
    prog = require('../package.json'),
    name = path.basename(process.argv[1], '.sh'),
    logger = require('./logger'),
    optimist = require('optimist'),
    yamljs = require('yamljs'),
    util = require('util'),
    fs = require('fs');


/**
 * Program configuration.
 *
 * <var>config</var> attributes will be updated with those read from <var>config_file</var>, if exists,
 * and from command line arguments, in that order.
 */
var config = {
    config_file: path.join(__dirname, '/../config', name + '.yml'),
    log_level: 'DEBUG',
    listen_port: 3000,
    web_context: '/',
    secret:'ssshhh',
    paths: {
        reports_url: '/report',
        reports_files: '/var/www/html/RegionSanityCheck'
    },
    cbroker: {
        host: 'localhost',
        port: '1026',
        path: '/NGSI10/queryContext'
    },
    idm: {
        host: 'account.lab.fiware.org',
        clientId: '',
        clientSecret: '',
        url: 'https://account.lab.fiware.org',
        callbackURL: 'http://fi-health.lab.fiware.org/login'
    },
    mailman: {
        host: 'localhost',
        port: '8000',
        path: '/',
        email_from: ''
    },
    jenkins: {
        host: 'localhost',
        port: '8000',
        token: '',
        path:'',
        parameterName:''
    },
    default: true
};



function readConfigFile(file) {
    try {
        var cfg_parse = yamljs.parse(fs.readFileSync(file, 'utf8'));
        var cfg_parser_result = [ 'INFO', 'Read configuration file' ];
        ['app','logging', 'session', 'paths', 'cbroker', 'idm', 'mailman','jenkins'].forEach(function (key) {
            switch (key in cfg_parse && key) {
                 case 'app':
                    config.listen_port = cfg_parse.app.port;
                    config.web_context = cfg_parse.app.web_context;
                    break;
                case 'logging':
                    config.log_level = cfg_parse.logging.level;
                    logger.setLevel(config.log_level)
                    break;
                case 'session':
                    config.secret = cfg_parse.session.secret;
                    break;
                case 'paths':
                    Object.keys(config.paths).filter(hasOwnProperty, cfg_parse.paths).forEach(function(key) {
                        config.paths[key] = cfg_parse.paths[key];
                    });
                    break;
                case 'cbroker':
                    Object.keys(config.cbroker).filter(hasOwnProperty, cfg_parse.cbroker).forEach(function(key) {
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
                case 'jenkins':
                    Object.keys(config.jenkins).filter(hasOwnProperty, cfg_parse.jenkins).forEach(function (key) {
                        config.jenkins[key] = cfg_parse.jenkins[key];
                    });
                    break;
                default:
                    throw new Error(util.format('no "%s" node found', key));
            }
        });
        config.default=false;
    } catch (err) {
        var msg = err.errno ? 'Could not read configuration file' : util.format('Configuration file: %s', err.message);
        cfg_parser_result = [ 'WARN', msg ];
    }

    // show result of configuration processing

    var log_function = logger[cfg_parser_result[0].toLowerCase()],
    log_message = cfg_parser_result[1];
    log_function(log_message);
    return cfg_parser_result;
}


function main() {
        // create argument parser
    var arg_parser = optimist.demand([])
        .options('h', { 'alias': 'help', 'describe': 'show help message and exit', 'boolean': true })
        .options('v', { 'alias': 'version', 'describe': 'show version and exit', 'boolean': true });


    // read configuration file if exists (path maybe taken from command line)
    arg_parser
        .options('c', {
            'alias': 'config-file', 'describe': 'configuration file', 'string': true,
            'default': config.config_file
        })
        .check(function (argv) {
            config.config_file = argv['config-file'];
        })
        .parse(process.argv);

    //process config file
    var cfg_parser_result=readConfigFile(config.config_file);

    // process command line arguments
    arg_parser
        .usage(util.format('Usage: %s [options]\n\n%s', name, prog.description))
        .options('l', {
            'alias': 'log-level', 'describe': 'logging level', 'string': true,
            'default': config.log_level
        })
        .options('p', {
            'alias': 'listen-port', 'describe': 'listen port',
            'default': config.listen_port
        })
        .check(function (argv) {
            if (argv.version) {
                console.error('%s v%s', name, prog.version);
                process.exit(1);
            } else if (argv.help) {
                optimist.showHelp();
                process.exit(0);
            } else Object.keys(argv).forEach(function (key) {
                var attr = key.replace('-', '_');
                if (attr in config) config[attr] = argv[key];
            });
        })
        .parse(process.argv);

    return config;
}


main();


/** @export */
module.exports.data = config;

/** @export */
module.exports.readConfigFile = readConfigFile;
