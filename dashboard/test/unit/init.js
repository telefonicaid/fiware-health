/*
 * Copyright 2016 Telefónica I+D
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

/* jshint unused: false */
var sinon = require('sinon'),
    path = require('path'),
    util = require('util'),
    configFile = path.join(__dirname, 'test_config.yml');


/** Fake command line arguments to load 'config' module with test configuration file */
process.argv = [ util.format('--config-file=%s', configFile) ];
require('../../lib/config');


/** Mock Jenkins API */
var jenkinsApi = require('jenkins-api'),
    jenkinsInit = sinon.stub(jenkinsApi, 'init').returns({}),
    jenkins = require('../../lib/jenkins');


/** @export */
exports.jenkinsApi = jenkinsApi;
