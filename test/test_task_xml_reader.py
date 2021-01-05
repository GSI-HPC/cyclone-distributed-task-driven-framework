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

from task.xml.task_xml_reader import TaskXmlReader
from task.task_factory import TaskFactory


def test_empty_task():

    task_xml_info = TaskXmlReader.read_task_definition('../Configuration/lustre_monitoring_tasks.xml', 'EmptyTask')
    task = TaskFactory().create_from_xml_info(task_xml_info)
    task.execute()


def test_io_task():

    task_xml_info = TaskXmlReader.read_task_definition('../Configuration/lustre_monitoring_tasks.xml', 'IOTask')
    task = TaskFactory().create_from_xml_info(task_xml_info)


def test_alert_io_task():

    task_xml_info = TaskXmlReader.read_task_definition('../Configuration/lustre_monitoring_tasks.xml', 'AlertIOTask')
    task = TaskFactory().create_from_xml_info(task_xml_info)


def main():

    try:

        test_empty_task()
        test_io_task()
        test_alert_io_task()

    except Exception as e:

        exc_type, exc_obj, exc_tb = sys.exc_info()
        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

        logging.error(f"Caught exception (type: {exc_type}): {e} - {filename} (line: {exc_tb.tb_lineno})")


if __name__ == '__main__':
    main()
