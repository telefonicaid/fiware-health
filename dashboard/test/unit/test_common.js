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
    common = require('../../lib/routes/common');


/* jshint multistr: true */
suite('common', function () {


    test('should_return_superuser_after_parse_roles_for_superuser_user', function () {
        //Given
        var roles=[{"name": "provider", "id": "1"}, {"name": "Superuser", "id": "xxxxxxxxxxxxxxx"}];

        //When
        var result=common.parseRoles(roles);

        //Then
        assert.equal('superuser', result);

    });


    test('should_return_read_only_after_parse_roles_for_common_user', function () {
        //Given
        var roles=[];

        //When
        var result=common.parseRoles(roles);

        //Then
        assert.equal('', result);

    });


    test('should_return_admin_region_after_parse_roles_for_admin_user', function () {
        //Given
        var roles=[{"name": "Admin", "id": "xxxxxxxxxxxxxxxxxxxx"}];

        //When
        var result=common.parseRoles(roles);

        //Then
        assert.equal('admin', result);

    });


    test('should_return_true_if_is_authorized_like_admin_for_region', function () {
        //Given
        var regions = [
            {node: 'RegionOne', status: 'NOK', timestamp: '2015/05/13 11:10 UTC'},
            {node: 'RegionTwo', status: 'OK', timestamp: '2015/05/13 11:10 UTC'},
            {node: 'RegionTree', status: 'N/A', timestamp: '2015/05/13 11:10 UTC'}
        ];
        var expected = [
            {node: 'RegionOne', status: 'NOK', timestamp: '2015/05/13 11:10 UTC', authorized:true},
            {node: 'RegionTwo', status: 'OK', timestamp: '2015/05/13 11:10 UTC', authorized:false},
            {node: 'RegionTree', status: 'N/A', timestamp: '2015/05/13 11:10 UTC', authorized:false}
        ];

        //When
        regions=common.addAuthorized(regions, 'admin-regionone');

        //Then
        assert.deepEqual(expected,regions);

    });


    test('should_return_true_if_is_authorized_like_admin_for_region_with_postfix', function () {
        //Given
         var regions = [
            {node: 'RegionOne1', status: 'NOK', timestamp: '2015/05/13 11:10 UTC'},
            {node: 'RegionOne', status: 'OK', timestamp: '2015/05/13 11:10 UTC'},
            {node: 'RegionTree', status: 'N/A', timestamp: '2015/05/13 11:10 UTC'}
        ];
        var expected = [
            {node: 'RegionOne1', status: 'NOK', timestamp: '2015/05/13 11:10 UTC', authorized:true},
            {node: 'RegionOne', status: 'OK', timestamp: '2015/05/13 11:10 UTC', authorized:true},
            {node: 'RegionTree', status: 'N/A', timestamp: '2015/05/13 11:10 UTC', authorized:false}
        ];

        //When
        regions=common.addAuthorized(regions, 'admin-regionone');

        //Then
        assert.deepEqual(expected,regions);

    });



    test('should_return_false_if_is_not_authorized_like_admin_for_region', function () {
        //Given
        var regions = [
            {node: 'RegionOne', status: 'NOK', timestamp: '2015/05/13 11:10 UTC'},
            {node: 'RegionTwo', status: 'OK', timestamp: '2015/05/13 11:10 UTC'},
            {node: 'RegionTree', status: 'N/A', timestamp: '2015/05/13 11:10 UTC'}

        ];

        var expected = [
            {node: 'RegionOne', status: 'NOK', timestamp: '2015/05/13 11:10 UTC',authorized:false},
            {node: 'RegionTwo', status: 'OK', timestamp: '2015/05/13 11:10 UTC',authorized:false},
            {node: 'RegionTree', status: 'N/A', timestamp: '2015/05/13 11:10 UTC',authorized:false}

        ];

        //When
        regions=common.addAuthorized(regions, 'admin-regionfour');

        //Then
        assert.deepEqual(expected,regions);
    });




});

