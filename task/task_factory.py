#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020 Gabriele Iannetti <g.iannetti@gsi.de>
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


import importlib
import inspect

from msg.base_message import BaseMessage


class TaskFactory:

    def __init__(self):
        pass

    @staticmethod
    def create_from_xml_info(xml_info):

        dynamic_module = importlib.import_module(xml_info.class_module)
        dynamic_class = getattr(dynamic_module, xml_info.class_name)

        arg_spec = inspect.getargspec(dynamic_class.__init__)

        arg_spec_args = arg_spec.args
        len_init_args = len(arg_spec_args)

        len_body_items = len(xml_info.class_properties)

        if len_init_args > 0:

            if arg_spec_args[0] != 'self':
                raise RuntimeError("Parameter self not found in class: '%s'" % xml_info.class_name)

        if (len_init_args-1) != len_body_items:

            raise RuntimeError("Signature of '%s::%s::init(%s)' has different size to provided property list of '%s'!"
                               % (xml_info.class_module,
                                  xml_info.class_name,
                                  arg_spec.args,
                                  xml_info.class_properties))

        # Skip the self argument at position 0
        arg_index = 1

        for property_name in xml_info.class_properties.keys():

            if property_name != arg_spec_args[arg_index]:

                raise RuntimeError("Signature of '%s::%s::init(%s)' does not contain property name '%s'!"
                                   % (xml_info.class_module, xml_info.class_name, arg_spec.args, property_name))

            arg_index += 1

        # TODO: Use a dynamic constructor initialization instead!
        # No dynamic constructor instantiation with Python 2.7 - Might be improved in Python 3?

        body_items = xml_info.class_properties.values()

        return TaskFactory._create_task(dynamic_class, body_items, len_body_items)

    @staticmethod
    def create_from_message(message):

        if not message:
            raise RuntimeError("Message object has not been initialized!")

        header_items = message.header.split(BaseMessage.field_separator)

        if len(header_items) != 5:
            raise RuntimeError("Invalid message header for a task creation found: %s" % message)

        task_module = header_items[1]
        task_class = header_items[2]
        task_ost_name = header_items[3]
        task_oss_name = header_items[4]

        body_items = None
        len_body_items = 0

        task = None

        if message.body:

            body_items = message.body.split(BaseMessage.field_separator)
            len_body_items = len(body_items)

        module = importlib.import_module(task_module)
        dynamic_class = getattr(module, task_class)

        task = TaskFactory._create_task(dynamic_class, body_items, len_body_items)

        task.ost_name = task_ost_name
        task.oss_name = task_oss_name

        return task

    @staticmethod
    def _create_task(dynamic_class, body_items, len_body_items):

        task = None

        if len_body_items == 0:
            task = dynamic_class()
        elif len_body_items == 1:
            task = dynamic_class(body_items[0])
        elif len_body_items == 2:
            task = dynamic_class(body_items[0], body_items[1])
        elif len_body_items == 3:
            task = dynamic_class(body_items[0], body_items[1], body_items[2])
        elif len_body_items == 4:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3])
        elif len_body_items == 5:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4])
        elif len_body_items == 6:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4],
                                 body_items[5])
        elif len_body_items == 7:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4],
                                 body_items[5], body_items[6])
        elif len_body_items == 8:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4],
                                 body_items[5], body_items[6], body_items[7])
        elif len_body_items == 9:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4],
                                 body_items[5], body_items[6], body_items[7], body_items[8])
        elif len_body_items == 10:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4],
                                 body_items[5], body_items[6], body_items[7], body_items[8], body_items[9])
        elif len_body_items == 11:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4],
                                 body_items[5], body_items[6], body_items[7], body_items[8], body_items[9],
                                 body_items[10])
        elif len_body_items == 12:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4],
                                 body_items[5], body_items[6], body_items[7], body_items[8], body_items[9],
                                 body_items[10], body_items[11])
        elif len_body_items == 13:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4],
                                 body_items[5], body_items[6], body_items[7], body_items[8], body_items[9],
                                 body_items[10], body_items[11], body_items[12])
        elif len_body_items == 14:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4],
                                 body_items[5], body_items[6], body_items[7], body_items[8], body_items[9],
                                 body_items[10], body_items[11], body_items[12], body_items[13])
        elif len_body_items == 15:
            task = dynamic_class(body_items[0], body_items[1], body_items[2], body_items[3], body_items[4],
                                 body_items[5], body_items[6], body_items[7], body_items[8], body_items[9],
                                 body_items[10], body_items[11], body_items[12], body_items[14])
        else:
            raise RuntimeError("No task instantiation supported for: '%s'!" % dynamic_class.__name__)

        return task
