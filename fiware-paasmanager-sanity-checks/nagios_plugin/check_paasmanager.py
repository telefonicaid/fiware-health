#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 Telefonica Investigación y Desarrollo, S.A.U
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

__version__          = '1.0.0'
__version_info__     = (tuple([int(num) for num in __version__.split('.')]),)
__description__      = 'PaaSManager Sanity Check for Nagios'
__long_description__ = '''

This program is an script to be used as Nagios Plugin to check the PaaSManager service status.
The result of the script will be written by STDOUT following Nagios specifications:
    - CRITICAL: If GET or DELETE HTTP requests were failed
    - OK: If GET or DELETE HTTP requests were succeeded


usage:
  {prog} [--os-tenant-id=VALUE] [--os-username=VALUE] [--os-password=VALUE] \
  [--os-region-name=VALUE] [--os-auth-url=VALUE]
  {prog} --help | --version


environment:
  OS_TENANT_NAME                default value for Tenant name
  OS_USERNAME                   default value for Username
  OS_PASSWORD                   default value for Password
  OS_REGION_NAME                default value for Region name
  OS_AUTH_URL                   default value for Keystone URL

'''

from argparse import ArgumentParser, RawTextHelpFormatter, Action
import os.path
import re

from paasmanager_client.client import PaaSManagerClient


prog   = os.path.splitext(os.path.basename(__file__))[0]

NAGIOS_SERVICE_STATUS_OK = 'OK'
NAGIOS_SERVICE_STATUS_WARNING = 'Warning'
NAGIOS_SERVICE_STATUS_CRITICAL = 'Critical'
NAGIOS_SERVICE_STATUS_UNKNOWN = 'Unknown'
NAGIOS_RETURN_CODES = {NAGIOS_SERVICE_STATUS_OK: 0,
                       NAGIOS_SERVICE_STATUS_WARNING: 1,
                       NAGIOS_SERVICE_STATUS_CRITICAL: 2,
                       NAGIOS_SERVICE_STATUS_UNKNOWN: 3}


class config:
    """Program configuration.

    `config` attributes will be updated with those read from environment variables and from command line arguments,
    in that order.
    """

    os_tenant_id = ''
    os_username = ''
    os_password = ''
    os_region_name = ''
    os_auth_url = ''


def create_nagios_response(nagios_service_status, information_text):
    """
    This function prints to STDOUT the expected data by Nagios, according to the parameters,
     and EXIT the main program thread
    :param nagios_service_status: Nagios Service Status
    :param information_text: Additional information (one line)
    :return: None
    """

    print "%s: %s" % (nagios_service_status, information_text)
    exit(NAGIOS_RETURN_CODES[nagios_service_status])


def check_paasmanager(username, password, tenant_id, auth_url, region_name):
    """
    Check PaaSManager:
        - Create new environment
        - Remove environment
    :param username: Username
    :param password: Password
    :param tenant_id: TenantId
    :param auth_url: Keystone endpoint
    :param region_name: Name of the region (to get PaaSManager endpoint from Keystone)
    :return: None
    """

    try:
        # Create PaaSManagerClient
        paasmanager_client = PaaSManagerClient(username, password, tenant_id, auth_url, region_name)

        response = paasmanager_client.getEnvironmentResourceClient().create_environment("QAEnv", "For testing purposes")
        if not response.ok:
            create_nagios_response(NAGIOS_SERVICE_STATUS_CRITICAL, "HTTP %s - %s" % (response.status_code,
                                                                                     response.content))

        response = paasmanager_client.getEnvironmentResourceClient().delete_environment("QAEnv")
        if not response.ok:
            create_nagios_response(NAGIOS_SERVICE_STATUS_CRITICAL, "HTTP %s - %s" % (response.status_code,
                                                                                     response.content))

        create_nagios_response(NAGIOS_SERVICE_STATUS_OK, "Requests SUCCEEDED")
    except Exception as exception:
        create_nagios_response(NAGIOS_SERVICE_STATUS_CRITICAL, exception.message)


def main():

    arg_parser = ArgumentParser(add_help=False)

    # process command line arguments (considering environment variables)
    class Formatter(RawTextHelpFormatter):

        def __init__(self, prog):
            super(Formatter, self).__init__(prog, max_help_position=32)

        def _format_action_invocation(self, action):
            result = super(Formatter, self)._format_action_invocation(action)
            return re.sub(r'(-\w) (\w+), (--.+) \2', '\g<1>, \g<3>=\g<2>', result).ljust(self._max_help_position - 8)

    class LogAction(Action):

        def __call__(self, parser, namespace, value, option=None):
            setattr(namespace, self.dest, value)

    arg_parser = ArgumentParser(
        parents=[arg_parser], formatter_class=Formatter, description=__description__,
        epilog=''.join(__long_description__.partition("environment:\n")[1:]).format(prog=prog).strip(),
        usage='%(prog)s [arguments]', version='{} v{}'.format(prog, __version__))

    arg_parser.add_argument(
        '-t', '--os-tenant-name', dest='os_tenant_id', metavar='VALUE', type=str,
        default=os.getenv('OS_TENANT_NAME', ''),
        help='TenantID [default=%(default)s]')

    arg_parser.add_argument(
        '-u', '--os-username', dest='os_username', metavar='VALUE', type=str,
        default=os.getenv('OS_USERNAME', ''),
        help='Username [default=%(default)s]')

    arg_parser.add_argument(
        '-p', '--os-password', dest='os_password', metavar='VALUE', type=str,
        default=os.getenv('OS_PASSWORD', ''),
        help='Password [default=%(default)s]')

    arg_parser.add_argument(
        '-r', '--os-region-name', dest='os_region_name', metavar='VALUE', type=str,
        default=os.getenv('OS_REGION_NAME', ''),
        help='Region name [default=%(default)s]')

    arg_parser.add_argument(
        '-a', '--os_auth_url', dest='os_auth_url', metavar='VALUE', type=str,
        default=os.getenv('OS_AUTH_URL', ''),
        help='Auth endpoint (Keystone) [default=%(default)s]')


    config.__dict__.update(arg_parser.parse_args().__dict__)

    # startup
    check_paasmanager(config.os_username, config.os_password, config.os_tenant_id, config.os_auth_url,
                      config.os_region_name)


if __name__ == '__main__':
    main()
