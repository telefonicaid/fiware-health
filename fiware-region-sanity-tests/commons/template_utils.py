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


from jinja2 import Template
import re
from argparse import ArgumentParser

HTML_START_BLOCK_PATTERN = ".*#SPLIT: (.*)#.*"
HTML_END_BLOCK_PATTERN = ".*#ENDSPLIT#.*"


def replace_template_properties(template, **kargs):
    """This method replaces all *kargs parameters (key=value) in the given template
    :param template: Temaplate to be rendered (String)
    :return: It will return the rendered template as unicode string.
    """
    template_obj = Template(template)
    return template_obj.render(kargs)


def split_html(html_to_split):
    """
    This method splits the given html in two pages. A new page will be built using the content mark as "to be splitted"
     in the first one. This content will be deleted in it.

        <!-- #SPLIT: ${OS_REGION_NAME}_failure_details.html#
            .... code to be used in the new web page ....
        #ENDSPLIT# -->

    :param html_to_split: Path with de original HTML file with SPLIT marks
    :return: None
    """

    # Open input file and read all lines
    input_file = open(html_to_split, "r")
    lines = input_file.readlines()
    input_file.close()

    # Open input file to remove split lines
    input_file = open(html_to_split, "w")
    output_file = None

    try:
        for line in lines:
            if re.match(HTML_START_BLOCK_PATTERN, line) and output_file is None:
                output_file_name = re.match(HTML_START_BLOCK_PATTERN, line).group(1)
                output_file = open(output_file_name, "w")
            elif re.match(HTML_END_BLOCK_PATTERN, line) and output_file is not None:
                output_file.close()
                output_file = None
            elif output_file is not None:
                output_file.write(line)
            else:
                input_file.write(line)
    finally:
        if input_file is not None:
            input_file.close()


if __name__ == '__main__':
    """
    Executes some utils.
        If --html-split is given, a new HTML page will be built using the content mark as "to be splitted"
        in the first one (this content will be deleted in the first)
    """
    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        '-s', '--html-split', dest='html_to_split', metavar='VALUE', type=str,
        default=None,
        help='Path to HTML file to be splitted [default=%(default)s]')


    args = arg_parser.parse_args()
    if args.html_to_split is not None:
        split_html(args.html_to_split)
