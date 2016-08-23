# How to execute:
# $ docker build -t fiwaredashboard .
# $ docker run -p 3000:3000 -d fiwaredashboard

FROM fiwarecentos:6.6
WORKDIR /opt
RUN yum -y install git
RUN curl --silent --location https://rpm.nodesource.com/setup_4.x | bash -
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
RUN yum -y install mailman python-pip
RUN RPM_FILE=$(find $WORKSPACE -name "*.rpm"); rpm -i $RPM_FILE
COPY dashboard/tools/docker/fihealth_dashboard.yml /etc/sysconfig/fihealth_dashboard.yml
COPY dashboard/tools/docker/settings.json /opt/fiware-health/dashboard/test/acceptance/conf/settings.json
WORKDIR /opt/fiware-health/dashboard/test/acceptance
RUN pip2.7 install -r requirements.txt
RUN pip2.7 install behave
CMD /etc/init.d/fihealth_dashboard start; (while ! nc -vn 127.0.0.1 3000; do sleep 1; done); behave features/ --tags ~@selenium --junit --junit-directory testreport

