# How to execute:
# - It is needed to configure some environment variables:
#   $ export BRANCH=develop
#   $ export OS_USERNAME_VALUE=<OpenStack username>
#   $ export OS_PASSWORD_VALUE=<OpenStack password>
#   $ export OS_TENANT_NAME_VALUE=<OpenStack tenant name>
#
# $ docker build -t fiware-dashboard-rpm .
# $ docker run --name fiware-dashboard-rpm fiware-dashboard-rpm

FROM fiwarecentos:6.6
WORKDIR /opt
RUN yum -y install git
RUN curl --silent --location https://rpm.nodesource.com/setup | bash -
RUN yum -y groupinstall 'Development Tools'
RUN yum -y install nodejs
RUN yum -y install rpm-build
RUN yum -y install initscripts
RUN yum -y install crontabs
RUN git clone https://github.com/telefonicaid/fiware-health /opt/fiware-health
ARG BRANCH=develop
RUN cd /opt/fiware-health; git checkout ${BRANCH}
WORKDIR /opt/fiware-health/dashboard
RUN npm install -g forever
RUN npm install -g grunt-cli
RUN npm install
RUN PROJECT_VERSION=$(sed -n '/"version"/ {s/.*:.*"\(.*\)".*/\1/; p; q}' package.json);tools/build/package.sh -v $PROJECT_VERSION
RUN yum clean all; yum -y install epel-release
RUN yum -y install mailman
RUN pip2.7 install http://repositories.lab.fiware.org/repo/files/fiware-repositories-uploadPkg-1.1.0.tar.gz
RUN RPM_FILE=$(find $WORKSPACE -name "*.rpm" -printf "%f");uploadPkg.py --os-username=$OS_USERNAME_VALUE --os-password=$OS_PASSWORD_VALUE --os-tenant-name=$OS_TENANT_NAME_VALUE $RPM_FILE
