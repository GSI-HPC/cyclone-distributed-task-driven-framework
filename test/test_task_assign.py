#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2021 Gabriele Iannetti <g.iannetti@gsi.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import os
import logging

from task.empty_task import EmptyTask
from msg.task_assign import TaskAssign


def test_empty_task_from_class():

    task = EmptyTask()
    task.tid = "0"
    task_assign = TaskAssign(task)

    print(f"test_empty_task_from_class: {task_assign.to_string()}")


def test_io_task_from_str():

    message = "TASK_ASS;task.io_task;IOTask;0;1000;1000000;off;target_dir;/usr/bin/lfs;fs-name"
    task_assign = TaskAssign(message)

    print(f"test_io_task_from_str: {task_assign.to_string()}")
    print(f"test_io_task_from_str.header: {task_assign.header}")
    print(f"test_io_task_from_str.body: {task_assign.body}")


def main():

    try:

        test_empty_task_from_class()
        test_io_task_from_str()

    except Exception as e:

        exc_type, _, exc_tb = sys.exc_info()
        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

        logging.error(f"Caught exception (type: {exc_type}): {e} - {filename} (line: {exc_tb.tb_lineno})")


if __name__ == '__main__':
    main()
