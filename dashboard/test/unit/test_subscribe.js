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
    subscribe = require('../../lib/routes/subscribe');


/* jshint multistr: true */
suite('subscribe', function () {


    test('should_searchSubscription_in_regions_list', function () {
        //given
        var user = "user@mail.com";
        var regions = [
            {node: 'region1', status: 'N/A'},
            {node: 'region2', status: 'OK'}
        ];
        //when
        subscribe.searchSubscription(user, regions, function () {
            assert(regions[0].subscribed);
            assert(!regions[1].subscribed);


        });
        //then


    });

    test('should_add_subscribed_to_true_in_isSubscribed_with_user_subscribed', function () {
        //given
        var user = "user@mail.com";
        var region = {node: 'region1'};
        //when
        subscribe.isSubscribed(user, region, function () {
            assert(region.subscribed);
        });
        //then


    });

    test('should_add_subscribed_to_false_in_isSubscribed_with_user_not_subscribed', function () {
        //given
        var user = "kk@mail.com";
        var region = {node: 'region1'};
        //when
        subscribe.isSubscribed(user, region, function () {
            assert(!region.subscribed);
        });
        //then


    });

    test('should_add_subscribed_to_false_in_isSubscribed_with_unknown_region', function () {
        //given
        var user = "kk@mail.com";
        var region = {node: 'unknown'};
        //when
        subscribe.isSubscribed(user, region, function () {
            assert(!region.subscribed);
        });
        //then


    });
});
