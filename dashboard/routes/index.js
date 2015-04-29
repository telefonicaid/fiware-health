var express = require('express');
var router = express.Router();
var dateFormat = require('dateformat');
var cbroker = require('./cbroker.js')

/* GET home page. */
router.get('/', function(req, res, next) {


  var regions=[{node:'spain', status: 'ok'}, {node:'trento',status:'fail'}];
  var timestamp=dateFormat(new Date(), "yyyy-mm-dd h:MM:ss");
  cbroker.postAllRegions(function (regions) {

  console.log("regions:"+regions);

  res.render('index', {timestamp:timestamp,regions: regions});

});

});

module.exports = router;
