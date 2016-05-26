FROM centos:6.6
WORKDIR /opt
RUN yum update -y
RUN yum install -y gcc git
RUN yum install -y wget tar
RUN yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel
RUN yum install -y openssh-server openssh-clients
RUN wget http://python.org/ftp/python/2.7.6/Python-2.7.6.tgz
RUN tar -xzf Python-2.7.6.tgz
RUN cd Python-2.7.6;./configure --prefix=/usr/local --enable-unicode=ucs4 --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
RUN cd Python-2.7.6;make && make altinstall
RUN wget --no-check-certificate http://pypi.python.org/packages/source/d/distribute/distribute-0.6.35.tar.gz
RUN tar xf distribute-0.6.35.tar.gz
RUN cd distribute-0.6.35;python2.7 setup.py install
RUN easy_install-2.7 pip
RUN pip2.7 install virtualenv
RUN yum install -y dbus-devel.x86_64 dbus-glib-devel.x86_64
RUN virtualenv fihealth --system-site-packages
RUN mkdir /opt/fihealth/src
WORKDIR /opt/fihealth/src
RUN echo "source /opt/fihealth/bin/activate" >>/etc/bashrc
RUN pip2.7 install python-config
# install dbus
RUN wget http://repositories.lab.fiware.org/repo/files/dbus-python-0.84.0.tar.gz
RUN tar -xf dbus-python-0.84.0.tar.gz
RUN source /opt/fihealth/bin/activate; cd dbus-python-0.84.0;./configure --prefix=/opt/fihealth
RUN source /opt/fihealth/bin/activate; cd dbus-python-0.84.0;make && make install
RUN yum -y install system-config-firewall
RUN service messagebus start

# install pygobject
RUN wget http://repositories.lab.fiware.org/repo/files/pygobject-2.20.0.tar.gz
RUN tar -xf pygobject-2.20.0.tar.gz
RUN source /opt/fihealth/bin/activate; cd pygobject-2.20.0;./configure --prefix=/opt/fihealth
RUN source /opt/fihealth/bin/activate; cd pygobject-2.20.0;make && make install

RUN mkdir /opt/fiware-health
ADD ./ /opt/fiware-health
WORKDIR /opt/fiware-health
RUN cp ./resources/docker/system.conf /etc/dbus-1/system.conf
RUN pip2.7 install -r requirements.txt --allow-all-external
EXPOSE 8081
COPY startspain2.sh start.sh
COPY key.pem key.pem
CMD start.sh ; ./../resources/docker/start.sh; 

