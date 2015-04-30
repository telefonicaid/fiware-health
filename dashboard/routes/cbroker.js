"use strict";
var http = require('http');
var cbroker = {};


var FIELDNAME = 'status'; // field name for value about regions status

cbroker.postAllRegions = function (callback) {


    var payload = {entities: [
        {type: "region", isPattern: "true", id: ".*"}
    ]};
    var payloadString = JSON.stringify(payload);
    var headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Content-Length': payloadString.length
    };
    var options = {
        host: '10.0.64.4',
        port: 1026,
        path: '/NGSI10/queryContext',
        method: 'POST',
        headers: headers
    };

    var req = http.request(options, function (res) {
        res.setEncoding('utf-8');
        var responseString = '';

        res.on('data', function (data) {
            responseString += data;
        });
        res.on('end', function () {
            var resultObject = JSON.parse(responseString);
            callback(cbroker.parseRegions(resultObject));
        });
    });
    req.on('error', function (e) {
        // TODO: handle error.
        console.log("Error");
        // only for testing end-to-end:
        var fs = require('fs');
        var json = JSON.parse(fs.readFileSync('./test/unit/post1.json', 'utf8'));
        console.log(json);
        callback(cbroker.parseRegions(json));
    });


    req.write(payloadString);
    req.end();

};


cbroker.parseRegions = function (json) {

    var result = [];

    var list = json.contextResponses;

    list.forEach(function (entry) {
        var type = entry.contextElement.type;
        if (type == 'region') {
            var timestamp = '';
            entry.contextElement.attributes.forEach(function (value) {
                if (value.name == FIELDNAME) {
                    timestamp = value.value;
                }
            });
            result.push({node: entry.contextElement.id, status: timestamp});
        }
    });


    return result;
};

module.exports = cbroker;
