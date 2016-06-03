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

from commons.constants import *
import paramiko
from paramiko import AuthenticationException
import StringIO
import socket
import time
import sys


class SSHClient:

    ssh_client = None

    def __init__(self, logger, host, username, private_key):
        """
        Inits attributes.
        :param logger: Logger object
        :param host: Server host name or IP (String)
        :param username: Username (String)
        :param private_key: RSA private key (String)
        :return: None
        """

        self.logger = logger
        self.host = host
        self.username = username
        self.private_key = private_key

        self.logger.debug("Initiating SSH Client. Host: %s, Username: %s", self.host, self.username)
        self.pkey = self.__generate_pkey_from_string__(self.private_key)

    @staticmethod
    def __generate_pkey_from_string__(private_key):
        """
        Generates a Paramiko PKey (PKey-class) from private key (String)
        :param private_key: Private key (String)
        :return: Paramiko PKey object
        """

        private_key_stream = StringIO.StringIO(private_key)
        pkey = paramiko.RSAKey.from_private_key(private_key_stream)
        private_key_stream.close()

        return pkey

    def connect(self):
        """
        Tries to connect (SSH) to the given HOST, username and private key, to port 22
        :return: None
        """

        self.logger.debug("Trying SSH connection to '%s'. Time out set to: %d", self.host, SSH_CONNECTION_TIMEOUT)
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(hostname=self.host, port=SSH_CONNECTION_PORT, username=self.username,
                                timeout=SSH_CONNECTION_TIMEOUT, pkey=self.pkey, look_for_keys=False)

    def connect_and_retry(self):
        """
        Tries to connect and retry MAX_WAIT_SSH_CONNECT_ITERATIONS times if a socket error is raised
        :return: None
        """

        self.logger.debug("Trying to establish a SSH connection to VM %s. Max. retries: %d", self.host,
                          MAX_WAIT_SSH_CONNECT_ITERATIONS)

        connected = False
        for i in range(MAX_WAIT_SSH_CONNECT_ITERATIONS):
            try:
                self.logger.debug("Attempt (#%d) for SSH connection to %s", i + 1, self.host)
                self.connect()
            except socket.error as e:
                self.logger.debug("SSH connection error. Error: %s; Message: %s", str(e.strerror), str(e.message))
            except AuthenticationException as e:
                self.logger.debug("Authentication exception: %s", str(e.message))
            else:
                connected = True
                self.logger.debug("Connected!")
                break
            time.sleep(SLEEP_TIME)

        if not connected:
            # Raise last exception captured
            raise sys.exc_info()[1]

    def close(self):
        """
        Closes the SSH connection
        :return: None
        """
        if self.ssh_client is not None:
            self.logger.debug("Closing SSH Client")
            self.ssh_client.close()
