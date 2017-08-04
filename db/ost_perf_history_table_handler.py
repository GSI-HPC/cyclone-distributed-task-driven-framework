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


import logging
import MySQLdb

from contextlib import closing


class OSTPerfHistoryTableHandler:

    def __init__(self, host, user, passwd, db, table_name):

        self._host = host
        self._user = user
        self._passwd = passwd
        self._db = db
        self._table_name = table_name

        self._ost_perf_result_list = list()

    def create_table(self):

        sql = """
CREATE TABLE """ + self._table_name + """ (
   id BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
   read_timestamp  TIMESTAMP NOT NULL DEFAULT "0000-00-00 00:00:00",
   write_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   ost CHAR(7) NOT NULL,
   ip CHAR(15) NOT NULL,
   size BIGINT(20) UNSIGNED NOT NULL,
   read_throughput BIGINT(20) UNSIGNED NOT NULL,
   write_throughput BIGINT(20) UNSIGNED NOT NULL,
   read_duration INT(10) UNSIGNED NOT NULL,
   write_duration INT(10) UNSIGNED NOT NULL,
   PRIMARY KEY (id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1
"""

        logging.debug("Creating database table:\n" + sql)

        with closing(MySQLdb.connect(host=self._host, user=self._user, passwd=self._passwd, db=self._db)) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(sql)

    def insert(self, ost_perf_result):

        if not ost_perf_result:
            raise RuntimeError('Insert failed with empty OST perf result object!')

        self._ost_perf_result_list.append(ost_perf_result)

    def store(self):

        len_ost_perf_result_list = len(self._ost_perf_result_list)

        sql = "INSERT INTO " \
            + self._table_name \
            + "(" \
            + "read_timestamp, " \
            + "write_timestamp, " \
            + "ost, " \
            + "ip, " \
            + "size, " \
            + "read_throughput, " \
            + "write_throughput, " \
            + "read_duration, " \
            + "write_duration" \
            + ") " \
            + "VALUES "

        if len_ost_perf_result_list > 0:

            sql += "(" + self._ost_perf_result_list[0].to_string_csv_list() + ")"

            if len_ost_perf_result_list > 1:

                for i in range(1, len_ost_perf_result_list):
                    sql += ",(" + self._ost_perf_result_list[i].to_string_csv_list() + ")"

        logging.debug("Executing SQL statement:\n" + sql)

        with closing(MySQLdb.connect(host=self._host, user=self._user, passwd=self._passwd, db=self._db)) as conn:
            with closing(conn.cursor()) as cur:

                cur.execute(sql)

                if cur.rowcount != len_ost_perf_result_list:
                    raise RuntimeError("Number of rows inserted is not equal to number of input records for table: %s"
                                       % self._table_name)

        # logging.debug("Inserted: %s records into table: %s" % (len_ost_perf_result_list, self._table_name))

    def count(self):
        return len(self._ost_perf_result_list)

    def clear(self):
        del self._ost_perf_result_list[:]
