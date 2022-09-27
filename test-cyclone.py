#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2022 Gabriele Iannetti <g.iannetti@gsi.de>
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import unittest

from msg.base_message import BaseMessage
from msg.task_assign import TaskAssign
from task.empty_task import EmptyTask
from task.task_factory import TaskFactory
from task.xml.task_xml_reader import TaskXmlReader

class TestTaskAssign(unittest.TestCase):

    def test_empty_task_from_class(self):

        task = EmptyTask()
        task.tid = "0"
        task_assign = TaskAssign(task)

        header = "TASK_ASS|task.empty_task|EmptyTask|0"
        body = None

        self.assertEqual(task_assign.header, header)
        self.assertEqual(task_assign.body, body)
        self.assertEqual(task_assign.to_string(), header)

    def test_io_task_from_str(self):

        header_task_type   = "TASK_ASS"
        header_task_module = "task.io_task"
        header_task_class  = "IOTask"
        header_task_id     = "23"

        header = f"{header_task_type}{BaseMessage.field_separator}   \
                   {header_task_module}{BaseMessage.field_separator} \
                   {header_task_class}{BaseMessage.field_separator}  \
                   {header_task_id}"

        body_ost_idx          = 348
        body_block_size_bytes = 1000
        body_total_size_bytes = 1000000
        body_write_file_sync  = "off"
        body_target_dir       = "target_dir"
        body_lfs_bin          = "lfs"
        body_lfs_target       = "fs-name"
        body_db_proxy_target  = "localhost"
        body_db_proxy_port    = 5777

        body = f"{body_ost_idx}{BaseMessage.field_separator}          \
                 {body_block_size_bytes}{BaseMessage.field_separator} \
                 {body_total_size_bytes}{BaseMessage.field_separator} \
                 {body_write_file_sync}{BaseMessage.field_separator}  \
                 {body_target_dir}{BaseMessage.field_separator}       \
                 {body_lfs_bin}{BaseMessage.field_separator}          \
                 {body_lfs_target}{BaseMessage.field_separator}       \
                 {body_db_proxy_target}{BaseMessage.field_separator}  \
                 {body_db_proxy_port}"

        message = header + BaseMessage.field_separator + body
        task_assign = TaskAssign(message)

        self.assertEqual(task_assign.header, header)
        self.assertEqual(task_assign.body, body)
        self.assertEqual(task_assign.to_string(), message)

class TestTaskXmlReader(unittest.TestCase):

    def test_empty_task(self):

        task_xml_info = \
            TaskXmlReader.read_task_definition('Configuration/lustre_ost_monitoring_tasks.xml', 'EmptyTask')

        task = TaskFactory().create_from_xml_info(task_xml_info)
        task.execute()

        self.assertEqual(task.tid, None)

    def test_io_task(self):

        task_xml_info = \
            TaskXmlReader.read_task_definition('Configuration/lustre_ost_monitoring_tasks.xml', 'IOTask')

        task = TaskFactory().create_from_xml_info(task_xml_info)

        self.assertEqual(task.write_file_sync, 'on')

    def test_lustre_file_creation_check_task(self):

        task_xml_info = \
            TaskXmlReader.read_task_definition('Configuration/lustre_ost_monitoring_tasks.xml', 'LustreFileCreationCheckTask')

        task = TaskFactory().create_from_xml_info(task_xml_info)

        self.assertEqual(task.pushgateway_timeout, 10000)

if __name__ == '__main__':
    unittest.main()
