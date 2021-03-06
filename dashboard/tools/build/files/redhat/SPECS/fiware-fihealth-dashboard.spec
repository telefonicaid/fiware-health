# Package installation custom attributes
%define _name fiware-fihealth-dashboard
%define _fiware_usr fiware
%define _fiware_grp fiware
%define _fiware_dir /opt/fiware
%define _dashboard_srv fihealth_dashboard
%define _dashboard_usr %{_fiware_usr}
%define _dashboard_grp %{_fiware_grp}
%define _dashboard_dir %{_fiware_dir}/%{_dashboard_srv}
%define _logging_dir /var/log/%{_dashboard_srv}
%define _forever_dir /var/run/fiware/.forever
%define _node_req_ver %(awk '/"node":/ {N=split($0,v,/["~=<>]/); print v[N-1]}' %{_basedir}/package.json)

# Package main attributes (_topdir, _basedir, _version and _release must be given at command line)
Summary: FIHealth Dashboard.
URL: https://github.com/telefonicaid/fiware-health/tree/master/dashboard
Name: %{_name}
Version: %{_version}
Release: %{_release}%{?dist}
License: Apache
Group: Applications/Engineering
Vendor: Telefónica I+D
BuildArch: noarch
Requires: mailman python python-pip
# nodejs dependency handled in 'pre' section (see below)

%description
Frontend for FIHealth Sanity Checks. Publishes an overview
page about the global status of FIWARE nodes, and provides
links to all test result reports.

%prep
# Clean build root directory
if [ -d $RPM_BUILD_ROOT ]; then
	rm -rf $RPM_BUILD_ROOT
fi

%clean
rm -rf $RPM_BUILD_ROOT

%install
mkdir -p $RPM_BUILD_ROOT/etc/sysconfig
mkdir -p $RPM_BUILD_ROOT/%{_dashboard_dir}; set +x
INCLUDE='bin|config|lib|package.json|README.*|.*rc$'
CFGFILE=config/dashboard.yml.sample
PATTERN='* .npmrc'
FILES=$(cd %{_basedir}; for i in $PATTERN; do echo $i; done | egrep "$INCLUDE")
for I in $FILES; do cp -R %{_basedir}/$I $RPM_BUILD_ROOT/%{_dashboard_dir}; done
cp %{_basedir}/$CFGFILE $RPM_BUILD_ROOT/etc/sysconfig/%{_dashboard_srv}.yml
cp -R %{_sourcedir}/* $RPM_BUILD_ROOT
(cd $RPM_BUILD_ROOT; find . -type f -printf "/%%P\n" >> %{_topdir}/MANIFEST)
echo "FILES:"; cat %{_topdir}/MANIFEST

%files -f %{_topdir}/MANIFEST
%config /etc/sysconfig/%{_dashboard_srv}.yml

%pre
# pre install ($1 == 1) or upgrade ($1 == 2)
if [ $1 -ge 1 ]; then
	NODE_REQ_VERSION=%{_node_req_ver}
	MAJOR=${NODE_REQ_VERSION%%%%.*}
	MINOR=$(expr ${NODE_REQ_VERSION%%.*} : '0\.\(.*\)' '|' 'x')

	# Function to compare version strings (in `x.y.z' format)
	valid_version() {
		local CUR=$1
		local REQ=$2
		printf "$CUR\n$REQ" \
		| awk '{split($0,v,"."); for (i in v) printf "%%05d ", v[i]; print}' \
		| sort | tail -1 | cat -E | fgrep -q $CUR'$'
	}

	# Function to setup EPEL and/or NodeSource repo (for the latest node.js version)
	setup_nodesource() {
		fmt --width=${COLUMNS:-$(tput cols)} 1>&2 <<-EOF

			ERROR: node.js >=v$NODE_REQ_VERSION is required. Setting up
			repositories to get the latest version ...
		EOF

		# prepare sources list configuration for the next `yum' command
		# (this requires removing the lock to allow access to the repositories configuration)
		find /var/lib/rpm -name "*.lock" -exec rm -f {} \;
		curl -sL https://rpm.nodesource.com/setup_$MAJOR.$MINOR | bash - >/dev/null
		if [ $? -eq 0 ]; then fmt --width=${COLUMNS:-$(tput cols)} 1>&2 <<-EOF

			Please run \`sudo yum -y install nodejs' to install/upgrade version
			prior reinstalling this package.

			EOF
		else fmt --width=${COLUMNS:-$(tput cols)} 1>&2 <<-EOF

			Unable to setup repositories. Please install/upgrade node.js manually
			and then reinstall this package.

			EOF
		fi
	}

	NODE_CUR_VERSION=$(node -pe 'process.versions.node' 2>/dev/null)
	if ! valid_version ${NODE_CUR_VERSION:-0.0.0} $NODE_REQ_VERSION; then
		setup_nodesource
		exit 1
	fi
	exit 0
fi

%post
# post install ($1 == 1) or upgrade ($1 == 2)
if [ $1 -ge 1 ]; then
	# actual values of installation variables
	FIWARE_USR=%{_fiware_usr}
	FIWARE_GRP=%{_fiware_grp}
	FIWARE_DIR=%{_fiware_dir}
	DASHBOARD_SRV=%{_dashboard_srv}
	DASHBOARD_USR=%{_dashboard_usr}
	DASHBOARD_GRP=%{_dashboard_grp}
	DASHBOARD_DIR=%{_dashboard_dir}
	LOGGING_DIR=%{_logging_dir}
	FOREVER_DIR=%{_forever_dir}
	STATUS=0

	# create additional directories
	mkdir -p $LOGGING_DIR
	mkdir -p $FOREVER_DIR

	# install npm dependencies
	echo "Installing npm dependencies ..."
	cd $DASHBOARD_DIR
	npm config set ca=""
	npm install --production || STATUS=1
	echo

	# install pip dependencies (in current python env or virtualenv)
	echo "Installing package dependencies ..."
	pip install mailman-api==0.2.9 -q || STATUS=1

	# check FIWARE user
	if ! getent passwd $FIWARE_USR >/dev/null; then
		groupadd --force $FIWARE_GRP
		useradd --gid $FIWARE_GRP --shell /bin/false \
		        --home-dir /nonexistent --no-create-home \
		        --comment "FIWARE" $FIWARE_USR
	fi

	# check DASHBOARD user
	if ! getent passwd $ADAPTER_USR >/dev/null; then
		groupadd --force $ADAPTER_GRP
		useradd --gid $ADAPTER_GRP --shell /bin/false \
		        --home-dir /nonexistent --no-create-home \
		        --comment "FIHealth Dashboard" $DASHBOARD_USR
	fi

	# change ownership
	chown -R $FIWARE_USR:$FIWARE_GRP $FIWARE_DIR
	chown -R $FIWARE_USR:$FIWARE_GRP $FOREVER_DIR
	chown -R $DASHBOARD_USR:$DASHBOARD_GRP $DASHBOARD_DIR
	chown -R $DASHBOARD_USR:$DASHBOARD_GRP $LOGGING_DIR

	# change file permissions
	chmod -R g+w $DASHBOARD_DIR
	chmod a+x $DASHBOARD_DIR/bin/dashboard

	# configure service
	chmod a+x /etc/init.d/$DASHBOARD_SRV
	/sbin/chkconfig --add $DASHBOARD_SRV

	# postinstall message
	if [ $STATUS -eq 0 ]; then fmt --width=${COLUMNS:-$(tput cols)} <<-EOF

		FIHealth Dashboard successfully installed at $DASHBOARD_DIR.

		WARNING: Please check values in the configuration file
		/etc/sysconfig/$DASHBOARD_SRV.yml before starting the
		\`$DASHBOARD_SRV' service. This must include the path to
		the settings file of Sanity Checks.

		In order to use mail notifications, some configuration steps
		should be done before running the Dashboard: please configure
		\`mailman' and \`mailman-api' first, and then execute (as
		superuser) the script $DASHBOARD_DIR/bin/setup passing the
		configuration file /etc/sysconfig/$DASHBOARD_SRV.yml as
		argument.

		EOF
	else fmt --width=${COLUMNS:-$(tput cols)} 1>&2 <<-EOF

		ERROR: Failed to install dependencies. Please check the error
		messages and then reinstall the package.

		EOF
	fi

	# finalization
	exit $STATUS
fi

%postun
# uninstall ($1 == 0)
if [ $1 -eq 0 ]; then
	# remove installation directory
	rm -rf %{_dashboard_dir}

	# remove FIWARE parent directory, if empty
	[ -d %{_fiware_dir} ] && rmdir --ignore-fail-on-non-empty %{_fiware_dir}

	# remove FIWARE Forever directory, if empty
	[ -d %{_forever_dir} ] && rmdir --ignore-fail-on-non-empty %{_forever_dir}

	# remove log files
	rm -rf %{_logging_dir}
fi

%changelog

* Thu Sep 28 2016 Telefónica I+D <opensource@tid.es> 1.11.0-1
- new contribution policy
- fix well parse	region name in title
- now compare username with region name instead of part of region name
- add transaction_id for traceability

* Thu Aug 25 2016 Telefónica I+D <opensource@tid.es> 1.10.0-1
- upgrade to nodejs 4.5.0
- change sleep function by setTimeout
- improve rpm spec file

* Tue Aug 09 2016 Telefónica I+D <opensource@tid.es> 1.9.1-1
- Add /show/:region API query

* Mon Jun 27 2016 Telefónica I+D <opensource@tid.es> 1.9.0-1
- fix jquery call. Due to use https, we have a problem using jquery
- add feature: new regions cache
- improve navigators/compatibility css in dashboard
- modify CSS style for non-data regions

* Thu May 31 2016 Telefónica I+D <opensource@tid.es> 1.8.0-1
- Use a separate subscription to get sanity_status values

* Thu May 3 2016 Telefónica I+D <opensource@tid.es> 1.7.0-1
- Progress status of sanity checks retrieved from Jenkins

* Mon Apr 04 2016 Telefónica I+D <opensource@tid.es> 1.6.0-1
- Add request to Monasca on notification from ContextBroker
- Fix timestamp handling
- Fix request to Monasca including value_meta
- Add elapsed time when publishing to Monasca
- Update documentation

* Mon Mar 07 2016 Telefónica I+D <opensource@tid.es> 1.5.0-1
- Add *.yml config file to /etc/sysconfig when packaging
- Fix file permissions
- Add new acceptance test with behave

* Wed Feb 03 2016 Telefónica I+D <opensource@tid.es> 1.4.0-1
- Add FIWARE SignOut library
- Fix checkstyle to avoid JShint errors.
- Add filter list to configuration

* Tue Dec 01 2015 Telefónica I+D <opensource@tid.es> 1.3.1-1
- Fix long name nodes.

* Mon Nov 30 2015 Telefónica I+D <opensource@tid.es> 1.3.0-1
- Timeout management for requests to Context Broker.

* Mon Oct 26 2015 Telefónica I+D <opensource@tid.es> 1.2.0-1
- Elapsed time of Sanity Checks execution
- Username of region administrators given by configuration
- Fix dependencies
- Add exclusions to sonar configuration
- Add jslint and gjslint support
- Fix documentation

* Mon Sep 28 2015 Telefónica I+D <opensource@tid.es> 1.1.3-1
- Bugfixing

* Tue Sep 08 2015 Telefónica I+D <opensource@tid.es> 1.1.2-1
- Documentation

* Tue Aug 04 2015 Telefónica I+D <opensource@tid.es> 1.1.1-1
- Required libs

* Tue Jun 30 2015 Telefónica I+D <opensource@tid.es> 1.1.0-1
- New css/style
- Add home button

* Thu Jun 03 2015 Telefónica I+D <opensource@tid.es> 1.0.0-2
- Add forever to monitor the execution of the server.

* Fri May 29 2015 Telefónica I+D <opensource@tid.es> 1.0.0-1
- New overview and details pages.
- IdM authentication.
- Mail notifications in subscriptions to status changes.
