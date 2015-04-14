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
# Launch testcase execution and generate reports
#
# Usage:
#     $0 [--verbose] [region ...]
#     $0 --help
#
# Options:
#     -v, --verbose	enable logging with verbose details
#     -h, --help	show this help message
#
# Regions:
#     Given by existing tests/regions/test_{region_name}.py files
#

OPTS='v(verbose)h(help)'
NAME=$(basename $0)

# nosetests options
TESTS=
NOSEOPTS="--logging-filter=TestCase,novaclient,neutronclient --logging-level=ERROR"

# Available regions
REGIONS=$(cd tests/regions; ls test_*.py | sed 's/test_\(.*\).py/\1/g')
REGIONS_PATTERN='^\('$(echo $REGIONS | sed 's/ /\\|/g')'\)$'

# Process command line
OPTERR=
OPTSTR=$(echo :-:$OPTS | sed 's/([a-zA-Z0-9]*)//g')
OPTHLP=$(sed -n '20,/^$/ { s/$0/'$NAME'/; s/^#[ ]\?//p }' $0 | head -n -2;
	for i in $REGIONS ""; do printf "    %s\n" $i; done)
while getopts $OPTSTR OPT; do while [ -z "$OPTERR" ]; do
case $OPT in
'v')	NOSEOPTS="$NOSEOPTS --logging-level=DEBUG";;
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
while [ -z "$OPTERR" -a -n "$1" ]; do
	REGION_NAME=$(expr "$1" : "$REGIONS_PATTERN") && shift
	[ -z "$REGION_NAME" ] && OPTERR="Invalid region '$1'"
	TESTS="$TESTS tests.regions.test_$REGION_NAME"
done
[ -n "$OPTERR" ] && {
	[ "$OPTERR" != "$OPTHLP" ] && OPTERR="${OPTERR}\nTry \`$NAME --help'"
	TAB=4; LEN=$(echo "$OPTERR" | awk -F'\t' '/ .+\t/ {print $1}' | wc -L)
	TABSTOPS=$TAB,$(((2+LEN/TAB)*TAB)); WIDTH=${COLUMNS:-$(tput cols)}
	printf "$OPTERR" | tr -s '\t' | expand -t$TABSTOPS | fmt -$WIDTH -s 1>&2
	exit 1
}
TESTS=${TESTS:-tests/regions}

# Main
nosetests $TESTS $NOSEOPTS -v --exe \
	--with-xunit --xunit-file=test_results.xml \
	--with-html --html-report=test_results.html \
	--html-report-template=resources/templates/test_report_template.html
