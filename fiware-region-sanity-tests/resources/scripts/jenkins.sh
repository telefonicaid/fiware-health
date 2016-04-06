#!/bin/sh
#
# Copyright 2013-2015 Telefónica I+D
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
#     -t, --htdocs=PATH			absolute path where to publish HTML
#     -a, --adapter-url=URL		endpoint of NGSI Adapter
#     -c, --cb-url=URL			endpoint of ContextBroker
#     -k, --workon-home=PATH		optional base path for virtualenv
#     -r, --os-region-name=NAME		optional region to restrict tests to
#     -l, --os-auth-url=URL		optional OpenStack auth_url (see below)
#     -u, --os-username=STRING		optional OpenStack username
#     -p, --os-password=STRING		optional OpenStack password
#     -i, --os-tenant-id=ID		optional OpenStack tenant_id
#     -n, --os-tenant-name=NAME		optional OpenStack tenant_name
#     -d, --os-user-domain-name=NAME	optional OpenStack user_domain_name (to
#     					replace the former if Identity API v3)
#
# Actions:
#     setup				Setup environment for Sanity Check
#     restart				Restart supporting servers (PhoneHome)
#     exec				Execution of Sanity Check for a region
#
# Environment:
#     JENKINS_HOME			home path of Jenkins CI
#     JOB_URL				full URL for this build job
#     TEST_PHONEHOME_ENDPOINT		endpoint of supporting PhoneHome server
#     FIHEALTH_WORKSPACE		default value for --workspace
#     FIHEALTH_HTDOCS			default value for --htdocs
#     FIHEALTH_ADAPTER_URL		default value for --adapter-url
#     FIHEALTH_CB_URL			default value for --cb-url
#     WORKON_HOME			default value for --workon-home
#     OS_REGION_NAME			default value for --os-region-name
#     OS_AUTH_URL			default value for --os-auth-url
#     OS_USERNAME			default value for --os-username
#     OS_PASSWORD			default value for --os-password
#     OS_TENANT_ID			default value for --os-tenant-id
#     OS_TENANT_NAME			default value for --os-tenant-name
#     OS_USER_DOMAIN_NAME		default value for --os-user-domain-name
#
# Requirements:
#     python2.7				Python 2.7 interpreter (found in path)
#     virtualenv			Python package 'virtualenv'
#
# OpenStack credentials:
#     Override those defined in 'settings.json', used by 'sanity_checks' script.
#

NAME=$(basename $0)
OPTS=`tr -d '\n ' <<END
      h(help)
      w(workspace):
      t(htdocs):
      a(adapter-url):
      c(cb-url):
      k(workon-home):
      r(os-region-name):
      l(os-auth-url):
      u(os-username):
      p(os-password):
      i(os-tenant-id):
      n(os-tenant-name):
      d(os-user-domain-name):
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
't')	FIHEALTH_HTDOCS=$OPTARG;;
'a')	FIHEALTH_ADAPTER_URL=$OPTARG;;
'c')	FIHEALTH_CB_URL=$OPTARG;;
'k')	WORKON_HOME=$OPTARG;;
'r')	OS_REGION_NAME=$OPTARG;;
'l')	OS_AUTH_URL=$OPTARG;;
'u')	OS_USERNAME=$OPTARG;;
'p')	OS_PASSWORD=$OPTARG;;
'i')	OS_TENANT_ID=$OPTARG;;
'n')	OS_TENANT_NAME=$OPTARG;;
'd')	OS_USER_DOMAIN_NAME=$OPTARG;;
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

# This function updates the value of the sanity_check_elapsed_time
# context attribute in ContextBroker with the time value
# given by params.
function update_elapsed_time_context_broker() {
	local sc_elapsed_time=$1
	local region=$OS_REGION_NAME

	printf "Updating elapsed time in Context Broker for $region. Elapsed time: $sc_elapsed_time. "
	curl $FIHEALTH_CB_URL/NGSI10/updateContext -o /dev/null -s -S \
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

# Change region status (when running tests on a single region). If a filename is
# given as argument $1, then status and all individual tests results are updated
# by NGSI Adapter according to that results report.
function change_status() {
	local region=$OS_REGION_NAME
	local status="N/A"
	local report=$1

	# Finish if no region is set
	[ -n "$region" ] || return 0

	# Change region status
	if [ -r "$report" ]; then
		# Adjust status according to results report
		local resource="sanity_tests?id=$region&type=region"
		printf "Request to NGSI Adapter to change region status ... "
		curl "$FIHEALTH_ADAPTER_URL/$resource" -o /dev/null -s -S \
		--write-out "HTTP %{http_code} result from %{url_effective}\n" \
		--header 'Content-Type: text/plain' --data-binary @$report

	else
		# Update region entity in ContextBroker
		local strstatus="'maintenance' (value="$status")"
		printf "Change region %s status to %s ... " $region "$strstatus"
		curl $FIHEALTH_CB_URL/NGSI10/updateContext -o /dev/null -s -S \
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
							"name": "sanity_status",
							"type": "string",
							"value": "$status"
						}
					]
				}
			],
			"updateAction": "APPEND"
		}
		EOF
	fi

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
if [ -z "$JENKINS_HOME" ]; then
	printf "Jenkins variable JENKINS_HOME missing\n" 1>&2
	exit 2
fi

if [ -z "$JOB_URL" ]; then
	printf "Jenkins variable JOB_URL missing (maybe not in a job?)\n" 1>&2
	exit 2
fi

# Check FIHealth environment variables for paths
if [ -z "$FIHEALTH_WORKSPACE" -o -z "$FIHEALTH_HTDOCS" ]; then
	printf "Either 'workspace' or 'htdocs' path not specified\n" 1>&2
	exit 3
fi

# Check FIHealth environment variables for endpoints
if [ -z "$FIHEALTH_ADAPTER_URL" -o -z "$FIHEALTH_CB_URL" ]; then
	printf "Either NGSI Adapter or ContextBroker URL not specified\n" 1>&2
	exit 3
fi

# Check FIHealth environment variables for Jenkins
if [ -z "$JENKINS_USER" -o -z "$JENKINS_PASSWORD" ]; then
	printf "Either Jenkins user or Jenkins password not specified\n" 1>&2
	exit 3
fi

# Check python2.7 and virtualenv
if ! which python2.7 virtualenv >/dev/null 2>&1; then
	printf "python2.7 or virtualenv not found\n" 1>&2
	exit 4
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
	# Start prepare action
	printf "Starting FIHealth Sanity Checks environment preparation ...\n"

	# Clean previous reports
	rm -f *_results.html *_results.xml *_results.txt

	# Clean and re-create virtualenv
	rm -rf $VIRTUALENV
	virtualenv -p python2.7 $VIRTUALENV

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

    # Update Restart job
	curl -X POST http://$JENKINS_USER:$JENKINS_PASSWORD@127.0.0.1:8080/job/FIHealth-SanityCheck-0-RestartTestServers/config.xml --data-binary "@resources/jenkins/FIHealth-SanityCheck-0-RestartTestServers.xml"

    # Update SetUp job
	curl -X POST http://$JENKINS_USER:$JENKINS_PASSWORD@127.0.0.1:8080/job/FIHealth-SanityCheck-0-SetUp/config.xml --data-binary "@resources/jenkins/FIHealth-SanityCheck-0-SetUp.xml"

	# Update Flow job
	curl -X POST http://$JENKINS_USER:$JENKINS_PASSWORD@127.0.0.1:8080/job/FIHealth-SanityCheck-1-Flow/config.xml --data-binary "@resources/jenkins/FIHealth-SanityCheck-1-Flow.xml"

	# Update Exec job
	curl -X POST http://$JENKINS_USER:$JENKINS_PASSWORD@127.0.0.1:8080/job/FIHealth-SanityCheck-2-Exec-Region/config.xml --data-binary "@resources/jenkins/FIHealth-SanityCheck-2-Exec-Region.xml"

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
	elapsed_time='N/A'

	# Start test action
	printf "Running %s ...\n" "$(./sanity_checks --version 2>&1)"

	# Optionally restrict tests to a region (leave empty for all)
	REGIONS=$OS_REGION_NAME
	OUTPUT_NAME=${OS_REGION_NAME:-test}_results

	# In single region tests, change status to 'Maintenance'
	change_status

	# Update 'sanity_check_elapsed_time' context attribute
	update_elapsed_time_context_broker $elapsed_time

	# Activate virtualenv
	source $VIRTUALENV/bin/activate

	# Execute tests
	export OS_AUTH_URL OS_USERNAME OS_PASSWORD
	export OS_TENANT_ID OS_TENANT_NAME OS_USER_DOMAIN_NAME

	# Get 'start_time' before executing Sanity Checks (milliseconds)
	start_time=$(date +%s%3N)

	./sanity_checks --verbose \
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
	cp -f $OUTPUT_NAME.html $FIHEALTH_HTDOCS
	cp -f $OUTPUT_NAME.txt $FIHEALTH_HTDOCS

	# In single region tests, change status according to results
	change_status $OUTPUT_NAME.txt
	;;
esac
