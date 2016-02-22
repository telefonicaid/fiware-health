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

from behave import step, then
import requests
from hamcrest import assert_that, is_, equal_to
import os


__author__ = "Telefonica I+D"
__copyright__ = "Copyright 2015"
__license__ = " Apache License, Version 2.0"


@step(u'the web server running properly')
def server_running_properly(context):
    """
    Step: Prepare server for running and check status.
    """
    pass


@step(u'I launch get operation')
def get(context):
    """
    Step: Launch get operation
    """

    if context.selenium:
        context.driver.get(context.dashboard_url)
    context.request = requests.get(context.dashboard_url)


@step(u'I receive a HTTP "(?P<status>\w*)" .*')
def http_status_code(context, status):
    """
    Step: Check the HTTP response status.
    """
    assert_that(str(context.request.status_code), is_(equal_to(status)),
                "HTTP response code is not the expected one.")


@step(u'the response title contains Sanity check status')
def response_title(context):
    """
    Step: Check the response title
    """
    assert_that(context.driver.title, is_(equal_to('Sanity check status')),
                "the response title is not the expected one.")
