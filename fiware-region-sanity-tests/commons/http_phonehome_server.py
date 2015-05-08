# -*- coding: utf-8 -*-

# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U
#
# This file is part of FIWARE project.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For those usages not covered by the Apache version 2.0 License please
# contact with opensource@tid.es

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import logging
import json
from os import environ
import sys
from commons.constants import PROPERTIES_FILE, PROPERTIES_CONFIG_TEST, PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT, \
    PHONEHOME_DBUS_NAME, LOGGING_FILE, PHONEHOME_DBUS_OBJECT_PATH
import urlparse
import re
from dbus_phonehome_service import DbusPhoneHomeServer
import logging.config


# Global DBus server instance
dbus_server = None


class HttpPhoneHomeRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        """
        Manages a POST request. Phonehome service.
          Emits a new DBus signal to the PhoneHome object published.
          The request always will return 200OK if some content is received. This content will be emitted in the signal.
        :return: None
        """

        global dbus_server

        content_length = int(self.headers['Content-Length'])
        content = self.rfile.read(content_length)

        # Get Hostname from body
        if content:
            dbus_server.emit_phonehome_signal(str(content))
            self.send_response(200)
        else:
            # Bad Request
            self.send_response(400, message="Invalid hostname received in HTTP PhoneHome request")


class HttpPhoneHomeServer():
    """
    This Server will be waiting for POST requests. If some request is received to '/' resource (root) will be
    processed. POST body is precessed using a DBus PhoneHome Client and 200OK is always returned.
    """

    def __init__(self, logger, port, timeout=None):
        """
        Creates a PhoneHome server
        :param logger: Logger
        :param port: Listen port
        :param timeout: Timeout to wait for some request. Only is used when 'single request server' is configured.
        :return: None
        """
        self.logger = logger
        self.logger.debug("Creating PhoneHome Server. Port %d; Timeout: %s", port, str(timeout))
        self.server = HTTPServer(('', port), HttpPhoneHomeRequestHandler)
        self.server.timeout = timeout

    def start_single_request(self):
        """
        Starts the server. Only waits for ONE request.
        :return:
        """
        self.logger.debug("Waiting for ONE call...")
        self.server.handle_request()

    def start_forever(self):
        """
        Starts the server. Forever...
        :return:
        """
        self.logger.debug("Waiting for calls...")
        self.server.serve_forever()

if __name__ == '__main__':

    logging.config.fileConfig(LOGGING_FILE)
    logger = logging.getLogger("HttpPhoneHomeServer")

    # Load properties
    logger.info("Loading test settings...")
    conf = dict()
    with open(PROPERTIES_FILE) as config_file:
        try:
            conf = json.load(config_file)
        except Exception as e:
            assert False, "Error parsing config file '{}': {}".format(PROPERTIES_FILE, e)

    # Check and load PhoneHome configuration (settings or env vars)
    conf_test = conf[PROPERTIES_CONFIG_TEST]
    phonehome_endpoint = environ.get('TEST_PHONEHOME_ENDPOINT', conf_test[PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT])
    env_conf = {
        PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT: phonehome_endpoint
    }
    conf[PROPERTIES_CONFIG_TEST].update(env_conf)

    if not phonehome_endpoint:
        logger.error("No value found for '%s.%s' setting. Phonehome server will NOT be launched",
                       PROPERTIES_CONFIG_TEST, PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT)
        sys.exit(1)

    phonehome_port = urlparse.urlsplit(phonehome_endpoint).port
    logger.info("PhoneHome port to be used by server: %d", phonehome_port)

    # Create global DBus server
    logger.info("Creating DBus PhoneHome service with object: %s", PHONEHOME_DBUS_OBJECT_PATH)
    dbus_server = DbusPhoneHomeServer(logger)
    dbus_server.register_phonehome_object(PHONEHOME_DBUS_OBJECT_PATH)

    # Create and start server
    logger.info("Creating and starting PhoneHome Server")
    server = HttpPhoneHomeServer(logger, phonehome_port)
    server.start_forever()
