/*
 * Copyright 2015-2016 Telefónica I+D
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
    cache = require('../../lib/cache');

/* jshint unused: false */
suite('cache', function () {

    test('should_return_1_when_first_argument_greater_than_second', function () {
        //given
        var a = 'Zregion';
        var b = 'Aregion';

        //when
        var result = cache.compare(a, b);

        //then
        assert(result === 1);
    });

    test('should_return_negative__when_first_argument_less_than_second', function () {
        //given
        var a = 'Aregion';
        var b = 'Zregion';

        //when
        var result = cache.compare(a, b);

        //then
        assert(result === -1);
    });

    test('should_return_0_when_first_argument_equal_than_second', function () {
        //given
        var a = 'Aregion';
        var b = 'Aregion';

        //when
        var result = cache.compare(a, b);

        //then
        assert(result === 0);
    });

});
