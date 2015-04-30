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

var assert = require('assert'),
    cbroker = require('../../lib/routes/cbroker.js'),
    fs = require('fs');


/* jshint multistr: true */
suite('cbroker', function () {


    test('should_have_a_postAllRegions_method', function () {
        assert.equal(typeof cbroker, 'object');
        assert.equal(typeof cbroker.postAllRegions, 'function');
    });

    test('should_return_a_json_with_all_regions_and_status', function () {
        //given
        var json = JSON.parse(fs.readFileSync('test/unit/post1.json', 'utf8'));
        //when
        var result = cbroker.parseRegions(json);
        //then
        var expected = [
            {node: 'Spain2', status: 'fail'},
            {node: 'Spain', status: 'ok'}
        ];

        assert.deepEqual(expected, result);

    });

});
