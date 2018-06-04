#!/bin/sh
#
# Copyright 2013-2016 Telefónica I+D
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
#     $0 [options] setup|restart|exec
#     $0 --help
#
# Options:
#     -h, --help			show this help message
#     -w, --workspace=PATH		absolute path of Jenkins job workspace
#     -y, --history=PATH		absolute path of history of executions
#     -t, --htdocs=PATH			absolute path where to publish HTML
#     -a, --adapter-url=URL		endpoint of NGSI Adapter
#     -c, --cb-url=URL			endpoint of ContextBroker
#     -k, --workon-home=PATH		optional base path for virtualenv
#     -r, --os-region-name=NAME		optional region to restrict tests to
#     -l, --os-auth-url=URL		optional OpenStack auth_url (see below)
#     -u, --os-username=STRING		optional OpenStack username
#     -p, --os-password=STRING		optional OpenStack password
#     -I, --os-user-id=ID		optional OpenStack user_id
#     -i, --os-tenant-id=ID		optional OpenStack tenant_id
#     -n, --os-tenant-name=NAME		optional OpenStack tenant_name
#     -d, --os-user-domain-name=NAME	optional OpenStack user_domain_name
#     -P, --os-project-domain-name=NAME	optional OpenStack project_domain_name
#
# Actions:
#     setup				Setup environment for Sanity Check
#     restart				Restart supporting servers (PhoneHome)
#     exec				Execution of Sanity Check for a region
#
# Environment:
#     JENKINS_HOME			home path of Jenkins CI
#     JENKINS_USER 			username of the Jenkins CI
#     JENKINS_PASSWORD			password of the Jenkins CI
#     JENKINS_URL			URL of the Jenkins CI
#     TEST_PHONEHOME_ENDPOINT		endpoint of supporting PhoneHome server
#     FIHEALTH_WORKSPACE		default value for --workspace
#     FIHEALTH_HISTORY			default value for --history
#     FIHEALTH_HTDOCS			default value for --htdocs
#     FIHEALTH_ADAPTER_URL		default value for --adapter-url
#     FIHEALTH_CB_URL			default value for --cb-url
#     WORKON_HOME			default value for --workon-home
#     OS_REGION_NAME			default value for --os-region-name
#     OS_AUTH_URL			default value for --os-auth-url
#     OS_USERNAME			default value for --os-username
#     OS_PASSWORD			default value for --os-password
#     OS_USER_ID			default value for --os-user-id
#     OS_TENANT_ID			default value for --os-tenant-id
#     OS_TENANT_NAME			default value for --os-tenant-name
#     OS_USER_DOMAIN_NAME		default value for --os-user-domain-name
#     OS_PROJECT_DOMAIN_NAME		default value for --os-project-domain-name
#
# Requirements:
#     python2.7				Python 2.7 interpreter (found in path)
#     virtualenv			Python package 'virtualenv'
#

NAME=$(basename $0)
OPTS=`tr -d '\n ' <<END
      h(help)
      w(workspace):
      y(history):
      t(htdocs):
      a(adapter-url):
      c(cb-url):
      k(workon-home):
      r(os-region-name):
      l(os-auth-url):
      u(os-username):
      p(os-password):
      I(os-user-id):
      i(os-tenant-id):
      n(os-tenant-name):
      d(os-user-domain-name):
      P(os-project-domain-name):
END`

# Command line options
ACTION=

# Process command line
OPTERR=
OPTSTR=$(echo :-:$OPTS | sed 's/([a-zA-Z0-9]*)//g')
OPTHLP=$(sed -n '20,/^$/ { s/$0/'$NAME'/; s/^#[ ]\?//p }' $0)
while getopts $OPTSTR OPT; do while [ -z "$OPTERR" ]; do
case $OPT in
'w')	FIHEALTH_WORKSPACE=$OPTARG;;
'y')	FIHEALTH_HISTORY=$OPTARG;;
't')	FIHEALTH_HTDOCS=$OPTARG;;
'a')	FIHEALTH_ADAPTER_URL=$OPTARG;;
'c')	FIHEALTH_CB_URL=$OPTARG;;
'k')	WORKON_HOME=$OPTARG;;
'r')	OS_REGION_NAME=$OPTARG;;
'l')	OS_AUTH_URL=$OPTARG;;
'u')	OS_USERNAME=$OPTARG;;
'p')	OS_PASSWORD=$OPTARG;;
'I')	OS_USER_ID=$OPTARG;;
'i')	OS_TENANT_ID=$OPTARG;;
'n')	OS_TENANT_NAME=$OPTARG;;
'd')	OS_USER_DOMAIN_NAME=$OPTARG;;
'P')	OS_PROJECT_DOMAIN_NAME=$OPTARG;;
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
ACTION=$(expr "$1" : "^\(setup\|restart\|exec\)$") && shift
[ -z "$OPTERR" -a -z "$ACTION" ] && OPTERR="Valid action required as argument"
[ -z "$OPTERR" -a -n "$*" ] && OPTERR="Too many arguments"
[ -n "$OPTERR" ] && {
	[ "$OPTERR" != "$OPTHLP" ] && OPTERR="${OPTERR}\nTry \`$NAME --help'"
	TAB=4; LEN=$(echo "$OPTERR" | awk -F'\t' '/ .+\t/ {print $1}' | wc -L)
	TABSTOPS=$TAB,$(((2+LEN/TAB)*TAB)); WIDTH=${COLUMNS:-$(tput cols)}
	printf "$OPTERR" | tr -s '\t' | expand -t$TABSTOPS | fmt -$WIDTH -s 1>&2
	exit 1
}

# Move reports of region $1 to history of executions, with timestamp prepended
function move_reports_to_history() {
	local region=$1
	local timestamp=$(ls -l --time-style='+%Y%m%d%H%M' ${region}_results.txt 2>/dev/null | cut -d' ' -f6)
	local histreport=$FIHEALTH_HISTORY/${timestamp}_${region}_results.txt
	if [ -n "$region" -a -n "$timestamp" -a -n "$FIHEALTH_HISTORY" ]; then
		printf "$region previous report stored as $histreport\n"
		mv ${region}_results.txt $histreport
		rm ${region}_results.*
	fi
}

# Update value of sanity_check_elapsed_time context attribute in ContextBroker
function update_elapsed_time_context_broker() {
	local sc_elapsed_time=$1
	local region=$OS_REGION_NAME

	printf "Updating elapsed time in Context Broker for $region. Elapsed time: $sc_elapsed_time. "
	curl $FIHEALTH_CB_URL/updateContext -o /dev/null -s -S \
	--write-out "HTTP %{http_code} result from %{url_effective}\n" \
	--header 'Content-Type: application/json' \
	--header 'Accept: application/json' --data @- <<-EOF
	{
		"contextElements": [
			{
				"type": "region",
				"isPattern": "false",
				"id": "$region",
				"attributes": [
				{
					"name": "sanity_check_elapsed_time",
					"type": "string",
					"value": "$sc_elapsed_time"
				}
				]
			}
		],
		"updateAction": "APPEND"
	}
	EOF
}

# Change region status (when running tests on a single region) according to the
# test results included in summary report file $1, by invoking NGSI Adapter.
function change_status() {
	local region=$OS_REGION_NAME
	local report=$1
	local txId=$2

	# Finish if no region is set or no report is given
	[ -n "$region" -a -r "$report" ] || return 0

	# Adjust status according to results report
	local resource="sanity_tests?id=$region&type=region"
	printf "Request txId=$txId to NGSI Adapter to change region status... "
	curl "$FIHEALTH_ADAPTER_URL/$resource" -o /dev/null -s -S \
	--write-out "HTTP %{http_code} result from %{url_effective}\n" \
	--header "Content-Type: text/plain" --header "txId: $txId" \
	--data-binary @$report

	return $?
}

# This function restarts PhoneHome server used for tests
function restart_phone_home_server() {
	local signal=TERM
	local logfile=/var/log/httpPhoneHomeServer.log
	[ "$1" == "--force" ] && signal=KILL
	pushd $PROJECT_DIR >/dev/null
	pkill -$signal -f http_phonehome_server
	export PYTHONPATH=$PWD
	nohup python2.7 commons/http_phonehome_server.py > $logfile 2>&1 &
	popd >/dev/null
}

# Main

# Check environment variables for Jenkins CI
if [ -z "$JENKINS_URL" ]; then
	printf "Environment variable JENKINS_URL not defined\n" 1>&2
	exit 2
elif [ -z "$(expr "$JENKINS_URL" : "^\(http://\)\S\S*:\S\S*\(/\S*\)\?$")" ]; then
	printf "Environment variable JENKINS_URL has a malformed value\n" 1>&2
	exit 2
elif [ -z "$JENKINS_USER" -o -z "$JENKINS_PASSWORD" ]; then
	printf "Either Jenkins user or password not specified\n" 1>&2
	exit 2
fi

# Check environment variables for paths
if [ -z "$JENKINS_HOME" ]; then
	printf "Environment variable JENKINS_HOME not defined\n" 1>&2
	exit 2
elif [ -z "$FIHEALTH_WORKSPACE" -o -z "$FIHEALTH_HTDOCS" ]; then
	printf "Either 'workspace' or 'htdocs' path not specified\n" 1>&2
	exit 2
fi

# Check FIHealth environment variables for endpoints
if [ -z "$FIHEALTH_ADAPTER_URL" -o -z "$FIHEALTH_CB_URL" ]; then
	printf "Either NGSI Adapter or ContextBroker URL not specified\n" 1>&2
	exit 2
fi

# Check python2.7 and virtualenv
if ! which python2.7 virtualenv >/dev/null 2>&1; then
	printf "python2.7 or virtualenv not found\n" 1>&2
	exit 3
fi

# Project name and root directory at Jenkins
PROJECT_NAME=fiware-region-sanity-tests
PROJECT_DIR=$FIHEALTH_WORKSPACE/$PROJECT_NAME

# Base path for virtualenv (assign default value if not set)
WORKON_HOME=${WORKON_HOME:=$HOME/venv}

# Python virtualenv
VIRTUALENV=$WORKON_HOME/$PROJECT_NAME

# Change to project directory
cd $PROJECT_DIR

# Perform action
case $ACTION in
setup)
	# Start "setup" action
	printf "Starting FIHealth Sanity Checks environment preparation ...\n"

	# Clean previous reports
	rm -f *_results.html *_results.xml *_results.txt

	# Clean and re-create virtualenv
	rm -rf $VIRTUALENV
	virtualenv -p python2.7 $VIRTUALENV

	# Create directory for history of executions, if needed
	[ -n "$FIHEALTH_HISTORY" ] && mkdir -p $FIHEALTH_HISTORY

	# Install dependencies in virtualenv
	source $VIRTUALENV/bin/activate
	pip install -r requirements.txt --allow-all-external

	# Install 'dbus-python' library in virtualenv
	mkdir -p $VIRTUALENV/src
	tar -C $VIRTUALENV/src -xzf $JENKINS_HOME/contrib/dbus-python-*.tar.gz
	cd $VIRTUALENV/src/dbus-python-*
	./configure --prefix=$VIRTUALENV
	make
	make install

	# Install 'pygobject' library in virtualenv
	mkdir -p $VIRTUALENV/src
	tar -C $VIRTUALENV/src -xzf $JENKINS_HOME/contrib/pygobject-*.tar.gz
	cd $VIRTUALENV/src/pygobject-*
	./configure --prefix=$VIRTUALENV
	make
	make install

	# Update Jenkins jobs
	cd $PROJECT_DIR
	BASE_JOB_URL=http://$JENKINS_USER:$JENKINS_PASSWORD@${JENKINS_URL#http://}/job
	for JOB_NAME in	FIHealth-SanityCheck-0-RestartTestServers \
			FIHealth-SanityCheck-0-SetUp \
			FIHealth-SanityCheck-1-Pipeline \
			FIHealth-SanityCheck-2-Exec-Region; do
		printf "Updating job '%s'...\n" $JOB_NAME
		curl -s -S -X POST $BASE_JOB_URL/$JOB_NAME/config.xml \
			--data-binary "@resources/jenkins/$JOB_NAME.xml"
	done

	# Restart PhoneHome server
	restart_phone_home_server
	;;

restart)
	# Activate virtualenv
	source $VIRTUALENV/bin/activate

	# Force restart of PhoneHome server
	restart_phone_home_server --force
	;;

exec)
	# Start test action
	printf "Build %s of %s ...\n" $BUILD_NUMBER "$(./sanity_checks --version 2>&1)"

	# Optionally restrict tests to a region (leave empty for all)
	REGIONS=$OS_REGION_NAME
	OUTPUT_NAME=${OS_REGION_NAME:-test}_results

	# In single region tests, move previous reports to history of executions
	move_reports_to_history $OS_REGION_NAME

	# Activate virtualenv
	source $VIRTUALENV/bin/activate

	# Execute tests
	export OS_AUTH_URL OS_USERNAME OS_PASSWORD OS_USER_ID
	export OS_TENANT_ID OS_TENANT_NAME OS_USER_DOMAIN_NAME OS_PROJECT_DOMAIN_NAME

	# Get 'start_time' before executing Sanity Checks (milliseconds)
	start_time=$(date +%s%3N)

	# Run sanity checks
	./sanity_checks --verbose \
		--build-number=$BUILD_NUMBER \
		--output-name=$OUTPUT_NAME \
		--template-name="dashboard_template.html" \
		$REGIONS

	# Get 'end_time' after executing Sanity Checks (milliseconds)
	end_time=$(date +%s%3N)

	# Get elapsed time of Sanity Checks execution
	elapsed_time=$(expr $end_time - $start_time)

	# Update 'sanity_check_elapsed_time' context attribute
	update_elapsed_time_context_broker $elapsed_time

	# Publish results to webserver
	[ -s $OUTPUT_NAME.html ] && cp -f $OUTPUT_NAME.html $FIHEALTH_HTDOCS
	[ -s $OUTPUT_NAME.txt ] && cp -f $OUTPUT_NAME.txt $FIHEALTH_HTDOCS

	# In case of single region tests, change status according to results
	[ -s $OUTPUT_NAME.txt ] && change_status $OUTPUT_NAME.txt $BUILD_NUMBER
	;;
esac
