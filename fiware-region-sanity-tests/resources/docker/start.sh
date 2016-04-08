#!/usr/bin/env bash

rm -rf /var/run/dbus/system_bus_socket;
service messagebus restart
export PYTHONPATH=$PWD
export TEST_PHONEHOME_ENDPOINT=http://localhost:8081
nohup python2.7 commons/http_phonehome_server.py > /var/log/httpPhoneHomeServer.log 2>&1&
tail -f /var/log/httpPhoneHomeServer.log