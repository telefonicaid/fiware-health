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


from commons.constants import PHONEHOME_DBUS_NAME, PHONEHOME_TIMEOUT, PHONEHOME_SIGNAL, PHONEHOME_METADATA_SIGNAL,\
    PHONEHOME_DBUS_OBJECT_METADATA_PATH, PHONEHOME_DBUS_OBJECT_PATH

from dbus import SystemBus
from dbus.exceptions import DBusException
from dbus.service import BusName
from dbus.mainloop.glib import DBusGMainLoop
import dbus
import gobject
import re


log_message_data_out_of_sequence =\
    "Received data are not for this FIWARE Node. Probably they come from another SanityCheck execution running "\
    "at the same time. Skipping and waiting for more data from PhoneHome Server..."


class DbusPhoneHomeClient:

    expected_signal_hostname = None
    mainloop = None
    data_received = None
    logger = None

    def __init__(self, logger):
        """Inits the DBus client and creates a new System bus
        :param logger: Logger
        :return:
        """

        self.logger = logger
        DbusPhoneHomeClient.logger = logger

        self.logger.debug("Attaching to a main loop")
        DBusGMainLoop(set_as_default=True)

        self.logger.debug("Creating session in SystemBus")
        self.bus = SystemBus()

    @staticmethod
    def timeout(mainloop, logger, *args):
        """Timeout function for DBus MainLoop
        :param mainloop: Loop manager (MainLoop)
        :param logger: Logger
        :param args: Rest of arguments
        :return: False. The function is called repeatedly until it returns FALSE,
         at which point the timeout is automatically destroyed and the function will not be called again.
        """
        logger.debug("Timed out!. Aborting the wait.")
        mainloop.quit()
        return False

    @staticmethod
    def phonehome_signal_handler(phonehome_http_data):
        """Handler for `PHONEHOME_SIGNAL`.
        :param phonehome_http_data: Data the VM emitted in the signal. If matches the expected one, main loop finishes.
        :return: None
        """
        DbusPhoneHomeClient.logger.debug("Data received from PhoneHome Server: '%s'",
                                         phonehome_http_data.encode('base64', 'strict').replace('\n', ' '))
        hostname = re.match(".*hostname=([\w-]*)", phonehome_http_data)
        hostname = hostname.group(1) if hostname is not None else hostname
        if DbusPhoneHomeClient.expected_signal_hostname == hostname:
            DbusPhoneHomeClient.logger.debug("Received hostname: '%s'",
                                             DbusPhoneHomeClient.expected_signal_hostname)
            DbusPhoneHomeClient.data_received = phonehome_http_data
            DbusPhoneHomeClient.mainloop.quit()
        else:
            DbusPhoneHomeClient.logger.debug(log_message_data_out_of_sequence)

    @staticmethod
    def phonehome_signal_handler_metadata(phonehome_http_data, hostname):
        """Handler for `PHONEHOME_METADATA_SIGNAL`.
        :param phonehome_http_data: Data the VM emitted in the signal.
        :param hostname: VM hostname. If matches the expected one, main loop finishes.
        :return: None
        """
        DbusPhoneHomeClient.logger.debug("Data received from PhoneHome Server (Hostname): '%s'",
                                         hostname.encode('base64', 'strict').replace('\n', ' '))

        if DbusPhoneHomeClient.expected_signal_hostname == hostname:
            DbusPhoneHomeClient.logger.debug("Received hostname: '%s'", hostname)
            DbusPhoneHomeClient.data_received = phonehome_http_data
            DbusPhoneHomeClient.mainloop.quit()
        else:
            DbusPhoneHomeClient.logger.debug(log_message_data_out_of_sequence)

    def connect_and_wait_for_phonehome_signal(self, bus_name, object_path, phonehome_signal, data_expected):
        """Connects to Bus and gets the published object (PhoneHome DBus object).
        :param bus_name: str
                A bus name (either the unique name or a well-known name)
                of the application owning the object. The keyword argument
                named_service is a deprecated alias for this. PhoneHome DBus service.
        :param object_path: str
                The object path of the desired PhoneHome Object.
        :param data_expected: The PhoneHome client will wait for `PHONEHOME_SIGNAL` with this data value.
         When received, main loop will be finished and data received from the signal will be returned.
        :return: None if signal has not been received after the timewait; Else, the content received in the signal
        """
        DbusPhoneHomeClient.data_received = None

        self.logger.debug("Connecting to PhoneHome DBus Service in bus '%s' and getting PhoneHome object "
                          "with path '%s'", bus_name, object_path)
        DbusPhoneHomeClient.expected_signal_hostname = data_expected

        try:
            object = self.bus.get_object(bus_name, object_path)
            phonehome_interface = dbus.Interface(object, bus_name)
        except DBusException as e:
            self.logger.error("PhoneHome bus or object not found. Please check the PhoneHome services. %s", str(e))
            return False

        # Connect to signal
        self.logger.debug("Connecting to signal '%s'", phonehome_signal)
        if phonehome_signal == PHONEHOME_SIGNAL:
            phonehome_interface.connect_to_signal(phonehome_signal, self.phonehome_signal_handler)
        elif phonehome_signal == PHONEHOME_METADATA_SIGNAL:
            phonehome_interface.connect_to_signal(PHONEHOME_METADATA_SIGNAL, self.phonehome_signal_handler_metadata)

        # Attach to a main loop
        self.logger.debug("Creating main loop")
        DbusPhoneHomeClient.mainloop = gobject.MainLoop()
        # Setup timeout and start main loop
        phonehome_timeout = PHONEHOME_TIMEOUT * 1000
        self.logger.debug("Setting time out to: %d", phonehome_timeout)
        gobject.timeout_add(phonehome_timeout, self.timeout, DbusPhoneHomeClient.mainloop, self.logger, priority=100)

        self.logger.debug("Waiting for signal '%s' with value or header 'hostname=%s' ."
                          " Timeout set to %s seconds", phonehome_signal, data_expected, PHONEHOME_TIMEOUT)
        DbusPhoneHomeClient.mainloop.run()
        self.logger.debug("Dbus PhoneHome Service stopped")

        return DbusPhoneHomeClient.data_received


class DbusPhoneHomeObject(dbus.service.Object):

    def __init__(self, logger, bus, object_path):
        """Creates and registers a new PhoneHome service in the bus.
        :param bus: BusName. The created DBus with well-known name.
        :param object_path: The object path of the desired PhoneHome Object.
        :return:
        """

        self.logger = logger
        self.bus = bus
        self.loop = None
        self.object_path = object_path

        self.logger.debug("Creating PhoneHome Object in the path '%s'", self.object_path)
        dbus.service.Object.__init__(self, self.bus, self.object_path)

    @dbus.service.signal(dbus_interface=PHONEHOME_DBUS_NAME, signature='s')
    def phonehome_signal(self, phonehome_http_data):
        """This method is used to emit `PHONEHOME_SIGNAL` with the given http data.
        :param phonehome_http_data: String with all BODY data of the POST request
        :return: None
        """

        self.logger.debug("PhoneHome signal emitted with data: %s", str(phonehome_http_data))

    @dbus.service.signal(dbus_interface=PHONEHOME_DBUS_NAME, signature='ss')
    def phonehome_metadata_signal(self, phonehome_http_data, hostname):
        """This method is used to emit `PHONEHOME_METADATA_SIGNAL` with the given http data.
        :param phonehome_http_data: String with all BODY data of the POST request
        :param hostname: String with the header hostname value.
        :return: None
        """

        self.logger.debug("PhoneHome Metadata signal emitted with data: %s for the hostname %s",
                          str(phonehome_http_data), hostname)

    def remove_object(self):
        """Makes this object inaccessible via the given D-Bus connection and object path:
         The object ceases to be accessible via any connection or path.
        :return: None
        """

        self.logger.debug("Removing object '%s' from connection", self.object_path)
        self.remove_from_connection(path=self.object_path)


class DbusPhoneHomeServer:

    def __init__(self, logger):
        """Initializes the DbusPhoneHomeServer.
        :param logger: Logger
        :return:
        """
        self.logger = logger
        self.dbus_phonehome_objects = {}

        self.logger.debug("Attaching to a main loop")
        DBusGMainLoop(set_as_default=True)

    def register_phonehome_object(self, phonehome_object_path):
        """Registers the bus name and a new phonehome object in this one.
        :param phonehome_object_path: The object path tho publish the desired PhoneHome Object. Format: /xxx/...
        :return: None
        """

        self.logger.debug("Registering new DBus name '%s'", PHONEHOME_DBUS_NAME)
        bus = BusName(PHONEHOME_DBUS_NAME, bus=SystemBus())

        self.logger.debug("Registering new PhoneHome Object '%s' in the Bus", phonehome_object_path)
        self.dbus_phonehome_objects[phonehome_object_path] = DbusPhoneHomeObject(self.logger, bus,
                                                                                 phonehome_object_path)

    def emit_phonehome_signal(self, phonehome_data, phonehome_object_path, hostname, transaction_id):
        """This method emits `PHONEHOME_SIGNAL` to all clients connected to the bus, with the given data as value.
        :param phonehome_data: PhoneHome data (HTTP POST request)
        :param hostname: String with the header Hostname value
        :param transaction_id: String with the transaction id value
        :return: None
        """
        self.logger.debug("%s - Emit signal, data:'%s' to '%s'", transaction_id, phonehome_data, hostname)

        if phonehome_object_path == PHONEHOME_DBUS_OBJECT_METADATA_PATH:
            self.dbus_phonehome_objects[phonehome_object_path].phonehome_metadata_signal(phonehome_data, hostname)
        elif phonehome_object_path == PHONEHOME_DBUS_OBJECT_PATH:
            self.dbus_phonehome_objects[phonehome_object_path].phonehome_signal(phonehome_data)

    def remove_object(self, phonehome_object_path):
        """Makes the PhoneHome object inaccessible via the given D-Bus connection and object path:
         The object ceases to be accessible via any connection or path.
        :return: None
        """
        self.dbus_phonehome_objects[phonehome_object_path].remove_object()

    def logdebug(self, trace):
        """Writes a debug log trace.
        :param trace: Message to trace
        :return: None
        """
        self.logger.debug(trace)
