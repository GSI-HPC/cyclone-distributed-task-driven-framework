#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

import inspect

from msg.base_message import BaseMessage
from msg.message_type import MessageType
from task.base_task import BaseTask
from task.task_factory import TaskFactory

class TaskAssign(BaseMessage):
    """The Master sends this message to a controller to assign a task."""

    """
        The __init__ method can take two different types of arguments:

        1. A string based object - if the controller retrieves this message from the master.
        2. A task based object - if the master sends this message to a controller.
    """
    def __init__(self, value):

        header = None
        body = None

        if not value:
            raise RuntimeError("No value object has been passed!")

        # Initialization by a passed string based object.
        if type(value) == str:

            message_items = value.split(BaseMessage.field_separator)
            count_message_items = len(message_items)
            len_message = len(value)

            if count_message_items < 4:
                raise RuntimeError(f"Invalid header size found in message: '{value}'")

            task_type   = message_items[0]
            task_module = message_items[1]
            task_class  = message_items[2]
            task_id     = message_items[3]

            header = \
                task_type   + BaseMessage.field_separator + \
                task_module + BaseMessage.field_separator + \
                task_class  + BaseMessage.field_separator + \
                task_id

            len_header = len(header)

            if len_header < len_message:
                body = value[len_header + 1:len_message]

        # Initialization by a passed task based object.
        else:

            task_class = value.__class__

            if not TaskAssign._is_inherited_from_base_task(task_class):
                raise RuntimeError(f"The following class was not inherited from the BaseTask class: '{task_class}'")

            header = TaskAssign._create_header(value, task_class)
            body = TaskAssign._create_body(value, task_class)

        super().__init__(header, body)

    @staticmethod
    def _is_inherited_from_base_task(a_class):

        if not a_class or len(a_class.__bases__) == 0:
            return False

        if a_class.__name__ == object.__name__:
            return False

        if a_class.__name__ == BaseTask.__name__:
            return True

        for base_class in a_class.__bases__:
            return TaskAssign._is_inherited_from_base_task(base_class)

    @staticmethod
    def _create_header(task, task_class):

        if not ("task." in task_class.__module__):
            raise RuntimeError("Task has to be located into the task package!")

        if not task.tid:
            raise RuntimeError(f"Attribute tid not set for task: {task_class}")

        header = \
            MessageType.TASK_ASSIGN() + BaseMessage.field_separator \
            + task_class.__module__   + BaseMessage.field_separator \
            + task_class.__name__     + BaseMessage.field_separator \
            + task.tid

        return header

    @staticmethod
    def _create_body(task, task_class):

        body = None

        args_list = inspect.getfullargspec(task_class.__init__).args
        len_args_list = len(args_list)

        # Skip first parameter 'self' of the __init__ method which is a convention in Python for that method.
        if len_args_list > 1:

            body = str(getattr(task, args_list[1]))

            if len_args_list > 2:

                # Ordering of the arguments from the __init__ method is relevant!
                # getattr throws an exception if an argument is not found in the task object.
                for index in range(2, len(args_list)):
                    body += BaseMessage.field_separator + str(getattr(task, args_list[index]))

        return body

    def to_task(self):
        return TaskFactory.create_from_message(BaseMessage(self.header, self.body))
