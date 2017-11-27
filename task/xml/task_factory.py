#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Gabriele Iannetti <g.iannetti@gsi.de>
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


class TaskFactory:

    def __init__(self):
        pass

    @staticmethod
    def create(class_module, class_name, class_properties_dict):

        dynamic_module = importlib.import_module(class_module)
        dynamic_class = getattr(dynamic_module, class_name)
        dynamic_object = None

        arg_spec = inspect.getargspec(dynamic_class.__init__)

        arg_spec_args = arg_spec.args
        len_init_args = len(arg_spec_args)

        len_class_properties = len(class_properties_dict)

        if len_init_args > 0:

            if arg_spec_args[0] != 'self':
                raise RuntimeError("Parameter self not found in class: '%s'" % class_name)

        if (len_init_args-1) != len_class_properties:

            raise RuntimeError("Signature of '%s::%s::init(%s)' has different size to provided property list of '%s'!"
                               % (class_module, class_name, arg_spec.args, class_properties_dict.keys()))

        # Skip the self argument at position 0
        arg_index = 1

        for property_name in class_properties_dict.keys():

            if property_name != arg_spec_args[arg_index]:

                raise RuntimeError("Signature of '%s::%s::init(%s)' does not contain property name '%s'!"
                                   % (class_module, class_name, arg_spec.args, property_name))

            arg_index += 1

        # No dynamic constructor instantiation with Python 2.7.
        # Current limitation is a constructor call with max. 12 arguments!
        # TODO: Might be improved in Python 3?

        prop_values = class_properties_dict.values()

        if len_class_properties == 1:
            dynamic_object = dynamic_class(prop_values[0])
        elif len_class_properties == 2:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1])
        elif len_class_properties == 3:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1], prop_values[2])
        elif len_class_properties == 4:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1], prop_values[2], prop_values[3])
        elif len_class_properties == 5:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1], prop_values[2], prop_values[3],
                                           prop_values[4])
        elif len_class_properties == 6:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1], prop_values[2], prop_values[3],
                                           prop_values[4], prop_values[5])
        elif len_class_properties == 7:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1], prop_values[2], prop_values[3],
                                           prop_values[4], prop_values[5], prop_values[6])
        elif len_class_properties == 8:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1], prop_values[2], prop_values[3],
                                           prop_values[4], prop_values[5], prop_values[6], prop_values[7])
        elif len_class_properties == 9:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1], prop_values[2], prop_values[3],
                                           prop_values[4], prop_values[5], prop_values[6], prop_values[7],
                                           prop_values[8])
        elif len_class_properties == 10:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1], prop_values[2], prop_values[3],
                                           prop_values[4], prop_values[5], prop_values[6], prop_values[7],
                                           prop_values[8], prop_values[9])
        elif len_class_properties == 11:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1], prop_values[2], prop_values[3],
                                           prop_values[4], prop_values[5], prop_values[6], prop_values[7],
                                           prop_values[8], prop_values[9], prop_values[10])
        elif len_class_properties == 12:
            dynamic_object = dynamic_class(prop_values[0], prop_values[1], prop_values[2], prop_values[3],
                                           prop_values[4], prop_values[5], prop_values[6], prop_values[7],
                                           prop_values[8], prop_values[9], prop_values[10], prop_values[11])
        else:
            raise RuntimeError("No object instantiation supported for: '%s::%s'!" % (class_module, class_name))

        return dynamic_object

