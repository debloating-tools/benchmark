# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import click

from . import core

INDENT = '    '
CMD_NAME_WIDTH = 24


def print_line(indent, name, help_msg=None):
    format_str = '{0}{1:<' + str(CMD_NAME_WIDTH - indent * len(INDENT)) + '}{2}'
    print(format_str.format(indent * INDENT, name, help_msg or ''))


def print_command_hierarchy(indent, click_commands_obj):
    for n, c in click_commands_obj.commands.items():
        if isinstance(c, click.core.Group):
            print_line(indent, n, '')
            print_command_hierarchy(indent + 1, c)
        elif isinstance(c, click.core.Command):
            print_line(indent, n, c.help)

        else:
            raise ValueError('Invalid object {}'.format(click_commands_obj))


@core.cli.command(help='Print all the commands')
def commands():
    print_command_hierarchy(0, core.cli)
