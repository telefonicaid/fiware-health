#!/bin/sh
#
# Copyright 2015 Telefónica I+D
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

#
# Support script for this component within a Jenkins CI job
#
# Usage:
#     $0 build|package
#     $0 --help
#
# Options:
#     -h, --help	show this help message
#
# Actions:
#     build		build, generate reports and publish to SonarQube
#     package		generate distribution package
#
# Environment:
#     JOB_URL		full URL for this build job
#     WORKSPACE		absolute path for build job's workspace
#

OPTS='h(help)'
NAME=$(basename $0)

# Command line options
ACTION=

# Process command line
OPTERR=
OPTSTR=$(echo :-:$OPTS | sed 's/([a-zA-Z0-9]*)//g')
OPTHLP=$(sed -n '20,/^$/ { s/$0/'$NAME'/; s/^#[ ]\?//p }' $0)
while getopts $OPTSTR OPT; do while [ -z "$OPTERR" ]; do
case $OPT in
'h')	OPTERR="$OPTHLP";;
'?')	OPTERR="Unknown option -$OPTARG";;
':')	OPTERR="Missing value for option -$OPTARG";;
'-')	OPTLONG="${OPTARG%=*}";
	OPT=$(expr $OPTS : ".*\(.\)($OPTLONG):.*" '|' '?');
	if [ "$OPT" = '?' ]; then
		OPT=$(expr $OPTS : ".*\(.\)($OPTLONG).*" '|' '?')
		OPTARG=-$OPTLONG
	else
		OPTARG=$(echo =$OPTARG | cut -d= -f3)
		[ -z "$OPTARG" ] && { OPTARG=-$OPTLONG; OPT=':'; }
	fi;
	continue;;
esac; break; done; done
shift $(expr $OPTIND - 1)
ACTION=$(expr "$1" : "^\(build\|package\)$") && shift
[ -z "$OPTERR" -a -z "$ACTION" ] && OPTERR="Valid action required as argument"
[ -z "$OPTERR" -a -n "$*" ] && OPTERR="Too many arguments"
[ -n "$OPTERR" ] && {
	[ "$OPTERR" != "$OPTHLP" ] && OPTERR="${OPTERR}\nTry \`$NAME --help'"
	TAB=4; LEN=$(echo "$OPTERR" | awk -F'\t' '/ .+\t/ {print $1}' | wc -L)
	TABSTOPS=$TAB,$(((2+LEN/TAB)*TAB)); WIDTH=${COLUMNS:-$(tput cols)}
	printf "$OPTERR" | tr -s '\t' | expand -t$TABSTOPS | fmt -$WIDTH -s 1>&2
	exit 1
}

# Main
if [ -z "$JOB_URL" -o -z "$WORKSPACE" ]; then
	printf "Jenkins variables JOB_URL and WORKSPACE are required\n" 1>&2
	exit 2
fi

# Project root at Jenkins workspace
PROJECT_DIR=$WORKSPACE/dashboard

# Absolute directories
LINT_REPORT_DIR=$PROJECT_DIR/report/lint
TEST_REPORT_DIR=$PROJECT_DIR/report/test
COVERAGE_REPORT_DIR=$PROJECT_DIR/report/coverage
COVERAGE_SITE_DIR=$PROJECT_DIR/site/coverage/lcov-report

# Properties
PRODUCT_INFO=$(awk '/"product"/,/\}/' $PROJECT_DIR/package.json)
PRODUCT_AREA=$(echo "$PRODUCT_INFO" | sed -n '/"area"/ {s/.*:.*"\(.*\)".*/\1/; p; q}')
PRODUCT_NAME=$(echo "$PRODUCT_INFO" | sed -n '/"name"/ {s/.*:.*"\(.*\)".*/\1/; p; q}')
PRODUCT_RELEASE=$(echo "$PRODUCT_INFO" | sed -n '/"release"/ {s/.*:.*"\(.*\)".*/\1/; p; q}')
PROJECT_NAME=$(sed -n '/"name"/ {s/.*:.*"\(.*\)".*/\1/; p; q}' $PROJECT_DIR/package.json)
PROJECT_DESC=$(sed -n '/"description"/ {s/.*:.*"\(.*\)".*/\1/; p; q}' $PROJECT_DIR/package.json)
PROJECT_VERSION=$(sed -n '/"version"/ {s/.*:.*"\(.*\)".*/\1/; p; q}' $PROJECT_DIR/package.json)
SONAR_PROJECT_NAME="FIHealth Dashboard"
SONAR_PROJECT_KEY=com.telefonica.iot:fihealth-dashboard

# Change to project directory
cd $PROJECT_DIR

# Perform action
case $ACTION in
build)
	# Install development dependencies
	sudo npm install -g grunt-cli
	npm install

	# Generate reports
	grunt lint-report test-report coverage-report

	# Fix reports with paths relative to $WORKSPACE root
	sed -i s:"$(readlink -f $PWD)":".":g $COVERAGE_REPORT_DIR/lcov.info

	# SonarQube coverage reports
	SONAR_COVERAGE_REPORT_RELATIVE_PATH=${COVERAGE_REPORT_DIR#$PROJECT_DIR/}/cobertura-coverage.xml
	SONAR_LCOV_REPORT_RELATIVE_PATH=${COVERAGE_REPORT_DIR#$PROJECT_DIR/}/lcov.info

	# Prepare properties file for SonarQube (awk to remove leading spaces)
	awk '$1=$1' > $PROJECT_DIR/sonar-project.properties <<-EOF
		product.area.name=$PRODUCT_AREA
		product.name=$PRODUCT_NAME
		product.release=$PRODUCT_RELEASE
		sonar.projectName=$SONAR_PROJECT_NAME
		sonar.projectKey=$SONAR_PROJECT_KEY
		sonar.projectVersion=$PROJECT_VERSION
		sonar.projectDescription=$PROJECT_DESC
		sonar.language=js
		sonar.sourceEncoding=UTF-8
		sonar.sources=lib/
		sonar.tests=test/
		sonar.exclusions=lib/public/javascripts/**.js,lib/www.js,lib/oauth2.js
		# coverage
		sonar.dynamicAnalysis=reuseReports
		sonar.cobertura.reportPath=$SONAR_COVERAGE_REPORT_RELATIVE_PATH
		sonar.javascript.lcov.reportPath=$SONAR_LCOV_REPORT_RELATIVE_PATH
	EOF

	# Generate metrics in SonarQube
	export DEBUG_METRICS=FALSE
	metrics_runner.sh
	;;

package)
	# install development dependencies
	if test -r /etc/redhat-release; then
		sudo yum -y -q install rpm-build redhat-rpm-config
	else
		sudo apt-get -y -q install dpkg-dev debhelper devscripts
	fi

	# Generate package
	$PROJECT_DIR/tools/build/package.sh -v $PROJECT_VERSION
	;;
esac
