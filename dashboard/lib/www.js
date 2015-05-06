#!/usr/bin/env node

/**
 * Module dependencies.
 */

var prog = require('../package.json'),
    app = require('./app'),
    debug = require('debug')('dashboard:server'),
    http = require('http'),
    logger = require('./logger'),
    util = require('util'),
    optimist = require('optimist'),
    yamljs = require('yamljs'),
    fs = require('fs');


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
        paths: {
            reports_files: '/var/www/html/RegionSanityCheck',
            reports_url: '/check/report'
        }
    };

exports.main = function () {

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
        ['logging', 'cbroker'].forEach(function (key) {
            switch (key in cfg_parse && key) {

                case 'logging':
                    config.log_level = cfg_parse.logging.level;
                    break;
                case 'cbroker':
                    Object.keys(config.cbroker).filter(hasOwnProperty, cfg_parse.cbroker).forEach(function (key) {
                        config.cbroker[key] = cfg_parse.cbroker[key];
                    });
                    break
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

    /**
     * Get port from environment and store in Express.
     */

    var port = normalizePort(process.env.PORT || '3000');
    app.set('port', port);


    /**
     * Create HTTP server.
     */

    var server = http.createServer(app);

    /**
     * Listen on provided port, on all network interfaces.
     */

    server.listen(port);
    server.on('error', onError);
    server.on('listening', onListening);

    logger.setLevel(config.log_level);
    logger.info('Started %s v%s\n%s', prog.name, prog.version, JSON.stringify(config, null, 2));

    /**
     * Normalize a port into a number, string, or false.
     */

    function normalizePort(val) {
        var port = parseInt(val, 10);

        if (isNaN(port)) {
            // named pipe
            return val;
        }

        if (port >= 0) {
            // port number
            return port;
        }

        return false;
    }

    /**
     * Event listener for HTTP server "error" event.
     */

    function onError(error) {
        if (error.syscall !== 'listen') {
            throw error;
        }

        var bind = typeof port === 'string'
            ? 'Pipe ' + port
            : 'Port ' + port;

        // handle specific listen errors with friendly messages
        switch (error.code) {
            case 'EACCES':
                logger.error(bind + ' requires elevated privileges');
                process.exit(1);
                break;
            case 'EADDRINUSE':
                logger.error(bind + ' is already in use');
                process.exit(1);
                break;
            default:
                throw error;
        }
    }

    /**
     * Event listener for HTTP server "listening" event.
     */

    function onListening() {
        var addr = server.address();
        var bind = typeof addr === 'string'
            ? 'pipe ' + addr
            : 'port ' + addr.port;
        logger.info('Listening on ' + bind);
    }


};

if (require.main === module) {
    exports.main();
    exports.cbroker = config.cbroker;
    exports.paths = config.paths;
}
