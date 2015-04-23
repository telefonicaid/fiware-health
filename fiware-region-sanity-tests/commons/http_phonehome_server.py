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

# Default timeout
DEFAULT_REQUEST_TIMEOUT = 60

# This global var will store the data received in the 'call' as String value (last call)
__phonehome_content__ = None


def reset_phonehome_content():
    """
    Resets 'callhome' variable to None
    :return: None
    """
    global __phonehome_content__
    __phonehome_content__ = None


def set_phonehome_content(value):
    """
    Sets a new value for 'callhome' variable
    :param value: Value to set
    :return: None
    """
    global __phonehome_content__
    __phonehome_content__ = value


def get_phonehome_content():
    """
    :return: callhome value (String)
    """
    content = __phonehome_content__
    return content


class HttpPhoneHomeRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        """
        Manages a POST request. Phonehome service.
        :return: None
        """
        global callhome
        content_length = int(self.headers['Content-Length'])
        set_phonehome_content(self.rfile.read(content_length))
        self.send_response(200)


class HttpPhoneHomeServer():
    """
    This Server will be waiting ONLY for one POST request. If some request is received to '/' resource (root) will be
    processed. POST body is saved __phonehome_content__ and 200OK is always returned.
    """

    def __init__(self, logger, port, timeout=DEFAULT_REQUEST_TIMEOUT):
        """
        Creates a PhoneHome server
        :param logger: Logger
        :param port: Listen port
        :param timeout: Timeout to wait for some request
        :return: None
        """
        self.logger = logger
        self.logger.debug("Creating PhoneHome Server. Port %d; Timeout: %d", port, timeout)
        self.server = HTTPServer(('', port), HttpPhoneHomeRequestHandler)
        self.server.timeout = timeout

    def start(self):
        """
        Starts the server.
        :return:
        """
        self.logger.debug("Waiting for call...")
        self.server.handle_request()
