#!/bin/sh
nosetests tests/regions --exe --with-xunit --xunit-file=test_results.xml --with-html --html-report=test_results.html --html-report-template=resources/templates/test_report_template.html -v
