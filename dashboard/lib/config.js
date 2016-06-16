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
    yaml = require('js-yaml'),
    util = require('util'),
    fs = require('fs'),
    cache = require('./cache');


/**
 * Program configuration.
 *
 * <var>config</var> attributes will be updated with those read from <var>configFile</var>, if exists,
 * and from command line arguments, in that order.
 */
var config = {
    configFile: path.join(__dirname, '/../config', name + '.yml'),
    logLevel: 'DEBUG',
    listenPort: 3000,
    webContext: '/',
    settings: 'config/settings.json.sample',
    secret: 'ssshhh',
    paths: {
        reportsUrl: '/report',
        reportsFiles: '/var/www/html/RegionSanityCheck'
    },
    cbroker: {
        host: 'localhost',
        port: '1026',
        path: '/NGSI10/queryContext',
        timeout: 10000,
        filter: []
    },
    idm: {
        host: 'account.lab.fiware.org',
        clientId: '',
        clientSecret: '',
        url: 'https://account.lab.fiware.org',
        logoutURL: 'https://account.lab.fiware.org/auth/logout',
        callbackURL: 'http://fi-health.lab.fiware.org/login',
        regionsAuthorized: []
    },
    mailman: {
        host: 'localhost',
        port: '8000',
        path: '/',
        emailFrom: ''
    },
    monasca: {
        host: 'localhost',
        port: '8070',
        keystoneHost: 'cloud.lab.fiware.org',
        keystonePort: '4731',
        keystonePath: '/v3/auth/tokens',
        keystoneUser: 'ceilometer',
        keystonePass: ''
    },
    jenkins: {
        host: 'localhost',
        port: '8000',
        token: '',
        path: '',
        parameterName: ''
    },
    default: true
};


function readConfigFile(file) {
    var cfgParserResult = [ 'INFO', 'Read configuration file' ];
    try {
        var cfgParse = yaml.safeLoad(fs.readFileSync(file, 'utf8'));
        var cfgKeys = ['app', 'logging', 'session', 'paths', 'cbroker', 'idm', 'mailman', 'monasca', 'jenkins'];
        cfgKeys.forEach(function (key) {
            switch (key in cfgParse && key) {
                case 'app':
                    config.listenPort = cfgParse.app.port;
                    config.webContext = cfgParse.app.webContext;
                    config.settings = cfgParse.app.settings;
                    config.fiHealthUrl = util.format('https://%s%s', cfgParse.app.host, cfgParse.app.webContext);
                    break;
                case 'logging':
                    config.logLevel = cfgParse.logging.level;
                    logger.setLevel(config.logLevel);
                    break;
                case 'session':
                    config.secret = cfgParse.session.secret;
                    break;
                case 'paths':
                    Object.keys(config.paths).filter(hasOwnProperty, cfgParse.paths).forEach(function(key) {
                        config.paths[key] = cfgParse.paths[key];
                    });
                    break;
                case 'cbroker':
                    Object.keys(config.cbroker).filter(hasOwnProperty, cfgParse.cbroker).forEach(function(key) {
                        config.cbroker[key] = cfgParse.cbroker[key];
                    });
                    break;
                case 'idm':
                    Object.keys(config.idm).filter(hasOwnProperty, cfgParse.idm).forEach(function (key) {
                        config.idm[key] = cfgParse.idm[key];
                    });
                    break;
                case 'mailman':
                    Object.keys(config.mailman).filter(hasOwnProperty, cfgParse.mailman).forEach(function (key) {
                        config.mailman[key] = cfgParse.mailman[key];
                    });
                    break;
                case 'monasca':
                    Object.keys(config.monasca).filter(hasOwnProperty, cfgParse.monasca).forEach(function (key) {
                        config.monasca[key] = cfgParse.monasca[key];
                    });
                    break;
                case 'jenkins':
                    Object.keys(config.jenkins).filter(hasOwnProperty, cfgParse.jenkins).forEach(function (key) {
                        config.jenkins[key] = cfgParse.jenkins[key];
                    });
                    var ctx = config.jenkins.path.replace(/(.*)\/job\/.+/, '$1');
                    config.jenkins.url = util.format('http://%s:%d%s', config.jenkins.host, config.jenkins.port, ctx);
                    break;
                default:
                    throw new Error(util.format('No "%s" node found', key));
            }
        });
        config.default = false;

    } catch (err) {
        var msg = err.errno ? 'Could not read configuration file' : util.format('Configuration file: %s', err.message);
        cfgParserResult = [ 'WARN', msg ];
    }

    // show result of configuration processing
    var logFunction = logger[cfgParserResult[0].toLowerCase()],
    logMessage = cfgParserResult[1];
    logFunction(logMessage);
    return cfgParserResult;
}


function main() {
    // create argument parser
    var argParser = optimist.demand([])
        .options('h', { 'alias': 'help', 'describe': 'show help message and exit', 'boolean': true })
        .options('v', { 'alias': 'version', 'describe': 'show version and exit', 'boolean': true });

    // read configuration file if exists (path maybe taken from command line)
    argParser
        .options('c', {
            'alias': 'config-file', 'describe': 'configuration file', 'string': true,
            'default': config.configFile
        })
        .check(function (argv) {
            config.configFile = argv['config-file'];
        })
        .parse(process.argv);

    // process config file
    readConfigFile(config.configFile);

    config.regions = cache;
    cache.init(config.settings);

    // process command line arguments
    argParser
        .usage(util.format('Usage: %s [options]\n\n%s', name, prog.description))
        .options('l', {
            'alias': 'log-level', 'describe': 'logging level', 'string': true,
            'default': config.logLevel
        })
        .options('p', {
            'alias': 'listen-port', 'describe': 'listen port',
            'default': config.listenPort
        })
        .check(function (argv) {
            if (argv.version) {
                console.error('%s v%s', name, prog.version);
                process.exit(1);
            } else if (argv.help) {
                optimist.showHelp();
                process.exit(0);
            } else {
                Object.keys(argv).forEach(function (key) {
                    var attr = key.replace(/(-)([a-z])/, function (str, $1, $2) { return $2.toUpperCase(); });
                    if (attr in config) {
                        config[attr] = argv[key];
                    }
                });
            }
        })
        .parse(process.argv);

    return config;
}


main();


/** @export */
module.exports.data = config;

/** @export */
module.exports.readConfigFile = readConfigFile;
