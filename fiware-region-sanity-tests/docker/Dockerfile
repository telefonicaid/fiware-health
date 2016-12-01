# How to:
# docker build -t fiwarehealth .
# docker run -p 8081:8081 -d fiwarehealth

FROM centos:6.6
WORKDIR /opt
RUN yum update -y && yum install -y dbus-devel.x86_64 dbus-glib-devel.x86_64 which   system-config-firewall gcc git wget tar zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel openssh-server openssh-clients
RUN wget http://python.org/ftp/python/2.7.6/Python-2.7.6.tgz
RUN tar -xzf Python-2.7.6.tgz
RUN cd Python-2.7.6;./configure --prefix=/usr/local --enable-unicode=ucs4 --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
RUN cd Python-2.7.6;make && make altinstall
RUN wget --no-check-certificate http://pypi.python.org/packages/source/d/distribute/distribute-0.6.35.tar.gz
RUN tar xf distribute-0.6.35.tar.gz
RUN cd distribute-0.6.35;python2.7 setup.py install
RUN easy_install-2.7 pip
RUN yum install -y dbus-devel.x86_64 dbus-glib-devel.x86_64
RUN pip2.7 install python-config python-openstackclient
RUN cp /usr/local/bin/python2.7-config /usr/bin/python-config
# install dbus
RUN wget http://repositories.lab.fiware.org/repo/files/dbus-python-0.84.0.tar.gz
RUN tar -xf dbus-python-0.84.0.tar.gz
ENV PYTHON_INCLUDES="-I/usr/local/include/python2.7"
ENV PYTHON_LIBS="-L/usr/local/lib -L /usr/lib"
ENV PYTHON="python2.7"
RUN cd dbus-python-0.84.0;./configure --prefix=/usr/local
RUN cd dbus-python-0.84.0;make && make install
RUN yum -y install system-config-firewall
RUN service messagebus start

# install pygobject
RUN wget http://repositories.lab.fiware.org/repo/files/pygobject-2.20.0.tar.gz
RUN tar -xf pygobject-2.20.0.tar.gz
RUN cd pygobject-2.20.0;PYTHON=/usr/local/bin/python2.7 ./configure --prefix=/usr/local
RUN cd pygobject-2.20.0;make && make install

RUN git clone https://github.com/telefonicaid/fiware-health /opt/fiware-health
WORKDIR /opt/fiware-health/fiware-region-sanity-tests
RUN cp ./resources/docker/system.conf /etc/dbus-1/system.conf
RUN pip2.7 install -r requirements.txt --allow-all-external
EXPOSE 8081
COPY settings.json etc/settings.json
CMD ./docker/start.sh
