var assert = require("assert");


var cbroker = require('../../routes/cbroker.js');
var fs = require('fs');

describe('contexBroker', function () {
    describe('#postAllRegions', function () {
        it('should have a postAllRegions method', function () {

            assert.equal(typeof cbroker, 'object');
            assert.equal(typeof cbroker.postAllRegions, 'function');
        });
    });
});


describe('contexBroker', function () {
    describe('#parseRegions', function () {
        it('should return a json with all regions and status', function () {

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
});
