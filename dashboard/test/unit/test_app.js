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
    app = require('../../lib/app');


/* jshint multistr: true */
suite('app', function () {


    test('should_return_superuser_after_parse_roles_for_superuser_user', function () {
        //Given
        var roles=[{"name": "provider", "id": "1"}, {"name": "Superuser", "id": "xxxxxxxxxxxxxxx"}];

        //When
        var result=app.parseRoles(roles);

        //Then
        assert.equal('superuser', result);

    });


    test('should_return_read_only_after_parse_roles_for_common_user', function () {
        //Given
        var roles=[];

        //When
        var result=app.parseRoles(roles);

        //Then
        assert.equal('', result);

    });


    test('should_return_admin_region_after_parse_roles_for_admin_user', function () {
        //Given
        var roles=[{"name": "Admin", "id": "xxxxxxxxxxxxxxxxxxxx"}];

        //When
        var result=app.parseRoles(roles);

        //Then
        assert.equal('admin', result);

    });



});

