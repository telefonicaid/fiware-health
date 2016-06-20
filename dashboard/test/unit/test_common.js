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
    init = require('./init'),
    common = require('../../lib/routes/common'),
    constants = require('../../lib/constants'),
    config = require('../../lib/config').data,
    _ = require('underscore');


/* jshint unused: false */
suite('common', function () {

    function fillCache(regions) {
        config.regions.flushAll();
        for (var index in regions) {
            config.regions.set(regions[index].node, {
                node: regions[index].node,
                status: regions[index].status,
                timestamp: regions[index].timestamp,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            });
        }
    }

    test('should_return_superuser_after_parse_roles_for_superuser_user', function () {
        //Given
        var roles = [{name: 'provider', id: '1'}, {name: 'Superuser', id: 'xxxxxxxxxxxxxxx'}];

        //When
        var result = common.parseRoles(roles);

        //Then
        assert.equal('superuser', result);

    });


    test('should_return_read_only_after_parse_roles_for_common_user', function () {
        //Given
        var roles = [];

        //When
        var result = common.parseRoles(roles);

        //Then
        assert.equal('', result);

    });


    test('should_return_admin_region_after_parse_roles_for_admin_user', function () {
        //Given
        var roles = [{name: 'Admin', id: 'xxxxxxxxxxxxxxxxxxxx'}];

        //When
        var result = common.parseRoles(roles);

        //Then
        assert.equal('admin', result);

    });


    test('should_return_true_if_is_authorized_like_admin_for_region', function () {
        //Given
        var regions = [
            {
                node: 'RegionOne',
                status: constants.GLOBAL_STATUS_NOT_OK,
                timestamp: '2015/05/13 11:10 UTC'
            },
            {
                node: 'RegionTwo',
                status: constants.GLOBAL_STATUS_OK,
                timestamp: '2015/05/13 11:10 UTC'
            },
            {
                node: 'RegionTree',
                status: constants.GLOBAL_STATUS_OTHER,
                timestamp: '2015/05/13 11:10 UTC'
            }
        ];
        var expected = [
            {
                node: 'RegionOne',
                status: constants.GLOBAL_STATUS_NOT_OK,
                timestamp: '2015/05/13 11:10 UTC',
                authorized: true,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            },
            {
                node: 'RegionTree',
                status: constants.GLOBAL_STATUS_OTHER,
                timestamp: '2015/05/13 11:10 UTC',
                authorized: false,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            },
            {
                node: 'RegionTwo',
                status: constants.GLOBAL_STATUS_OK,
                timestamp: '2015/05/13 11:10 UTC',
                authorized: false,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            }
        ];
        fillCache(regions);


        //When
        common.addAuthorized('admin-regionone');

        //Then
        regions = config.regions.list();
        assert(_.isEqual(expected, regions));

    });


    test('should_return_true_if_is_authorized_like_admin_for_region_with_postfix', function () {
         //Given
         var regions = [
            {
                node: 'RegionOne1',
                status: constants.GLOBAL_STATUS_NOT_OK,
                timestamp: '2015/05/13 11:10 UTC'
            },
            {
                node: 'RegionOne',
                status: constants.GLOBAL_STATUS_OK,
                timestamp: '2015/05/13 11:10 UTC'
            },
            {
                node: 'RegionTree',
                status: constants.GLOBAL_STATUS_OTHER,
                timestamp: '2015/05/13 11:10 UTC'
            }
        ];
        var expected = [
            {
                node: 'RegionOne',
                status: constants.GLOBAL_STATUS_OK,
                timestamp: '2015/05/13 11:10 UTC',
                authorized: true,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            },
            {
                node: 'RegionOne1',
                status: constants.GLOBAL_STATUS_NOT_OK,
                timestamp: '2015/05/13 11:10 UTC',
                authorized: true,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            },
            {
                node: 'RegionTree',
                status: constants.GLOBAL_STATUS_OTHER,
                timestamp: '2015/05/13 11:10 UTC',
                authorized: false,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            }
        ];
        fillCache(regions);

        //When
        common.addAuthorized('admin-regionone');

        //Then
        regions = config.regions.list();
        assert(_.isEqual(expected, regions));

    });


    test('should_return_true_if_is_authorized_like_admin_for_region_with_username_in_config_list', function () {
         //Given
         var regions = [
            {
                node: 'RegionOne1',
                status: constants.GLOBAL_STATUS_NOT_OK,
                timestamp: '2015/05/13 11:10 UTC'
            },
            {
                node: 'RegionOne',
                status: constants.GLOBAL_STATUS_OK,
                timestamp: '2015/05/13 11:10 UTC'
            },
            {
                node: 'RegionTree',
                status: constants.GLOBAL_STATUS_OTHER,
                timestamp: '2015/05/13 11:10 UTC'
            }
        ];
        var expected = [
            {
                node: 'RegionOne',
                status: constants.GLOBAL_STATUS_OK,
                timestamp: '2015/05/13 11:10 UTC',
                authorized: true,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            },
            {
                node: 'RegionOne1',
                status: constants.GLOBAL_STATUS_NOT_OK,
                timestamp: '2015/05/13 11:10 UTC',
                authorized: true,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            },
            {
                node: 'RegionTree',
                status: constants.GLOBAL_STATUS_OTHER,
                timestamp: '2015/05/13 11:10 UTC',
                authorized: false,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN
            }
        ];
        fillCache(regions);
        var data = [{'RegionOne': 'admin1'}, {'RegionOne1': 'admin-with-name'}, {'RegionOne': 'admin-with-name'}];
        config.idm.regionsAuthorized = data;

        //When
        common.addAuthorized('admin-with-name');

        //Then
        regions = config.regions.list();
        assert(_.isEqual(expected, regions));
        config.idm.regionsAuthorized = [];


    });



    test('should_return_false_if_is_not_authorized_like_admin_for_region', function () {
        //Given
        var regions = [
            {
                node: 'RegionOne',
                status: constants.GLOBAL_STATUS_NOT_OK,
                timestamp: '2015/05/13 11:10 UTC'
            },
            {
                node: 'RegionTwo',
                status: constants.GLOBAL_STATUS_OK,
                timestamp: '2015/05/13 11:10 UTC'
            },
            {
                node: 'RegionTree',
                status: constants.GLOBAL_STATUS_OTHER,
                timestamp: '2015/05/13 11:10 UTC'
            }
        ];
        var expected = [
            {
                authorized: false,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN,
                node: 'RegionOne',
                status: constants.GLOBAL_STATUS_NOT_OK,
                timestamp: '2015/05/13 11:10 UTC'
            },
            {
                authorized: false,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN,
                node: 'RegionTree',
                status: constants.GLOBAL_STATUS_OTHER,
                timestamp: '2015/05/13 11:10 UTC'
            },
            {
                authorized: false,
                elapsedTime: 'NaNh, NaNm, NaNs',
                elapsedTimeMillis: NaN,
                node: 'RegionTwo',
                status: constants.GLOBAL_STATUS_OK,
                timestamp: '2015/05/13 11:10 UTC'
            }
        ];
        fillCache(regions);

        //When
        common.addAuthorized('admin-regionfour');

        //Then
        regions = config.regions.list();
        assert(_.isEqual(expected, regions));
    });

});
