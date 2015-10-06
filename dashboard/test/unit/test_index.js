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
    sinon = require('sinon'),
    cbroker = require('../../lib/routes/cbroker'),
    index = require('../../lib/routes/index');




/* jshint multistr: true */
suite('index', function () {


     test('test_get_index', function () {

         //given

         var req = sinon.stub();
         var res = sinon.stub();
         var cbrokerStub = sinon.stub(cbroker, 'retrieveAllRegions');


        //when
        index.getIndex(req, res);

        //then
         assert(cbrokerStub.calledOnce);
         cbrokerStub.restore();


    });


});
