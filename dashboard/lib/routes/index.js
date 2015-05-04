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

var express = require('express'),
    router = express.Router(),
    dateFormat = require('dateformat'),
    cbroker = require('./cbroker');

/* GET home page. */
router.get('/', function (req, res) {


    var timestamp = dateFormat(new Date(), 'yyyy-mm-dd h:MM:ss');
    cbroker.postAllRegions(function (regions) {

        console.log('regions:' + regions);

        res.render('index', {title: 'FIWARE Regions - Sanity check', timestamp: timestamp, regions: regions});

    });

});

/** @export */
module.exports = router;
