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

import cherrypy
from cherrypy import _cperror
import httplib
import logging
import json
from os import environ
import sys
from commons.constants import PROPERTIES_FILE, PROPERTIES_CONFIG_TEST, PROPERTIES_CONFIG_TEST_PHONEHOME_ENDPOINT, \
    LOGGING_FILE_PHONEHOME, PHONEHOME_DBUS_OBJECT_PATH, PHONEHOME_DBUS_OBJECT_METADATA_PATH, PHONEHOME_TX_ID_HEADER
import urlparse
from dbus_phonehome_service import DbusPhoneHomeServer
import logging.config
import uuid


# Global DBus server instance
dbus_server = None

# Global logger
logging.config.fileConfig(LOGGING_FILE_PHONEHOME)
logger = logging.getLogger("HttpPhoneHomeServer")


class PhoneHome:
    exposed = True

    @cherrypy.tools.accept(media='text/plain')
    def POST(self):
        """
        Manages a POST request. Phonehome service.
          Emits a new DBus signal to the PhoneHome object published.
          The request always will return 200OK if some content is received. This content will be emitted in the signal.
        :return: None
        """

        global dbus_server

        content_length = int(cherrypy.request.headers['Content-Length'])
        content = cherrypy.request.body.read(content_length)

        logger.info("%s: %s - POST: ", PHONEHOME_TX_ID_HEADER, cherrypy.request.transaction_id)

        path = cherrypy.request.path_info

        # Get data from body
        if content:
            if path == PHONEHOME_DBUS_OBJECT_METADATA_PATH:

                if "Hostname" in cherrypy.request.headers:
                    hostname = cherrypy.request.headers['Hostname']

                    dbus_server.logdebug("{0}: {1} - Sending signal to hostname: {2}".format(
                        PHONEHOME_TX_ID_HEADER, cherrypy.request.transaction_id, hostname))

                    dbus_server.emit_phonehome_signal(str(content), PHONEHOME_DBUS_OBJECT_METADATA_PATH,
                                                      hostname, cherrypy.request.transaction_id)

                    cherrypy.response.status = httplib.OK
                    return
                else:
                    cherrypy.response.status = httplib.BAD_REQUEST
                    return "{0}: {1} - Hostname header is not present in HTTP PhoneHome request".format(
                        PHONEHOME_TX_ID_HEADER, cherrypy.request.transaction_id)

            elif path == PHONEHOME_DBUS_OBJECT_PATH:
                dbus_server.logdebug("{0}: {1} - Sending signal".format(PHONEHOME_TX_ID_HEADER,
                                                                       cherrypy.request.transaction_id))
                dbus_server.emit_phonehome_signal(str(content), PHONEHOME_DBUS_OBJECT_PATH, None,
                                                  cherrypy.request.transaction_id)
                cherrypy.response.status = httplib.OK
                return
            else:
                cherrypy.response.status = httplib.NOT_FOUND
                return "{0}: {1} - Path not found for HTTP PhoneHome request".format(
                    PHONEHOME_TX_ID_HEADER, cherrypy.request.transaction_id)

        else:
            # Bad Request
            cherrypy.response.status = httplib.BAD_REQUEST
            return "{0}: {1} - Invalid data received in HTTP PhoneHome request".format(
                    PHONEHOME_TX_ID_HEADER, cherrypy.request.transaction_id)


def handle_error():
    cherrypy.response.status = httplib.INTERNAL_SERVER_ERROR
    cherrypy.response.body = "Internal Server Error"
    print(_cperror.format_exc())


class Root(object):

    _cp_config = {'request.error_response': handle_error}
    pass


def before_request_body():
    """
    Add a Tool to our new Toolbox.
    """
    logger.info("before_request_body: %s ", cherrypy.request.params)
    if PHONEHOME_TX_ID_HEADER in cherrypy.request.headers:
        transaction_id = cherrypy.request.headers[PHONEHOME_TX_ID_HEADER]
    elif PHONEHOME_TX_ID_HEADER in cherrypy.request.params:
        transaction_id = cherrypy.request.params[PHONEHOME_TX_ID_HEADER]
        cherrypy.request.params = {}
    else:
        transaction_id = str(uuid.uuid1())

    cherrypy.request.transaction_id = transaction_id
    logger.info("%s: %s - before_request_body, path: %s", PHONEHOME_TX_ID_HEADER, cherrypy.request.transaction_id,
                cherrypy.request.path_info)

    request = cherrypy.serving.request

    def processor(entity):
        """Important! Do nothing with body"""
        if not entity.headers.get("Content-Length", ""):
            raise cherrypy.HTTPError(411)

        try:
            content_length = int(cherrypy.request.headers['Content-Length'])
            logger.info("%s: %s - body - content_length: %s ", PHONEHOME_TX_ID_HEADER, cherrypy.request.transaction_id,
                        content_length)

        except ValueError:
            raise cherrypy.HTTPError(400, 'Invalid Content-Length')

    request.body.processors['application/x-www-form-urlencoded'] = processor


def on_end_request():
    """
    After each request
    """
    logger.info("%s: %s - on_end_request", PHONEHOME_TX_ID_HEADER, cherrypy.request.transaction_id)
    print 'end'


class HttpPhoneHomeServer:
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
        self.timeout = timeout
        self.port = port

    def start_forever(self):
        """
        Starts the server. Forever...
        :return:
        """
        self.logger.debug("Waiting for calls...")
        conf = {
            'global': {
                'server.socket_host': '0.0.0.0',
                'server.socket_port': self.port,
                'tools.newprocessor_open.on': True,
                'tools.newprocessor_close.on': True,
            },
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'response.timeout': self.timeout,
                'tools.sessions.on': True,
                'tools.response_headers.on': True,
                'tools.response_headers.headers': [('Content-Type', 'text/plain')],
            }

        }
        root = Root()
        root.phonehome = PhoneHome()
        root.metadata = PhoneHome()

        cherrypy.tools.newprocessor_open = cherrypy.Tool('before_request_body', before_request_body, priority=100)
        cherrypy.tools.newprocessor_close = cherrypy.Tool('on_end_request', on_end_request)
        cherrypy.log.error_log.propagate = False
        cherrypy.log.access_log.propagate = False
        cherrypy.log.screen = None
        cherrypy.quickstart(root, '/', conf)

if __name__ == '__main__':

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
    logger.info("Creating DBus PhoneHome service with object: %s", PHONEHOME_DBUS_OBJECT_METADATA_PATH)
    dbus_server = DbusPhoneHomeServer(logger)
    dbus_server.register_phonehome_object(PHONEHOME_DBUS_OBJECT_PATH)
    dbus_server.register_phonehome_object(PHONEHOME_DBUS_OBJECT_METADATA_PATH)

    # Create and start server
    logger.info("Creating and starting PhoneHome Server")
    server = HttpPhoneHomeServer(logger, phonehome_port)
    server.start_forever()
