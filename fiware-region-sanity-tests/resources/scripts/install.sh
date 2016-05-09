yum update -y
yum -y groupinstall "Development tools"
yum -y install  gcc git  wget tar zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel
cd /opt; wget http://python.org/ftp/python/2.7.6/Python-2.7.6.tar.xz
tar xf Python-2.7.6.tar.xz
cd /opt/Python-2.7.6; ./configure --prefix=/usr/local --enable-unicode=ucs4 --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
cd /opt/Python-2.7.6; make && make altinstall

cd /opt;  wget  https://bootstrap.pypa.io/ez_setup.py;
/usr/local/bin/python2.7 ez_setup.py
/usr/local/bin/easy_install-2.7 pip
cp /usr/local/bin/pip2.7 /usr/bin/pip2.7
cp /usr/local/bin/python2.7 /usr/bin/python2.7

pip2.7 install /usr/local/bin/pip2.7
/usr/local/bin/virtualenv /opt/fihealth --system-site-packages
source /opt/fihealth/bin/activate
cd /opt
wget --no-check-certificate http://pypi.python.org/packages/source/d/distribute/distribute-0.6.35.tar.gz
tar xf distribute-0.6.35.tar.gz
cd distribute-0.6.35;python2.7 setup.py install
yum install -y dbus-devel.x86_64 dbus-glib-devel.x86_64
pip2.7 install python-config

cd /opt
wget http://repositories.lab.fiware.org/repo/files/dbus-python-0.84.0.tar.gz
tar -xf dbus-python-0.84.0.tar.gz
source /opt/fihealth/bin/activate; cd dbus-python-0.84.0;./configure --prefix=/opt/fihealth
source /opt/fihealth/bin/activate; cd dbus-python-0.84.0;make && make install
yum -y install system-config-firewall

service messagebus restart

# install pygobject
cd /opt; wget http://repositories.lab.fiware.org/repo/files/pygobject-2.20.0.tar.gz
tar -xf pygobject-2.20.0.tar.gz
cd /opt/pygobject-2.20.0;./configure --prefix=/opt/fihealth
cd /opt/pygobject-2.20.0;make && make install

git clone  https://github.com/telefonicaid/fiware-health /opt/fiware-health
cd /opt/fiware-health/fiware-region-sanity-tests
cp resources/docker/system.conf /etc/dbus-1/system.conf
pip2.7 install -r requirements.txt --allow-all-external
./resources/docker/start.sh
