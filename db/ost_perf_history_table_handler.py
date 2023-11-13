#!/usr/bin/env python3
#
# -*- coding: utf-8 -*-
#
# © Copyright 2023 GSI Helmholtzzentrum für Schwerionenforschung
#
# This software is distributed under
# the terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file "LICENCE".

from contextlib import closing

import logging
import mysql.connector

class OSTPerfHistoryTableHandler:

    def __init__(self, host, user, password, database, table):

        self._host = host
        self._user = user
        self._password = password
        self._database = database
        self._table = table

        self._ost_perf_result_list = list()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self

    def create_table(self):

        sql = """
CREATE TABLE """ + self._table + """ (
   id BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
   read_timestamp  TIMESTAMP NOT NULL DEFAULT "0000-00-00 00:00:00",
   write_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   ost CHAR(7) NOT NULL,
   size BIGINT(20) UNSIGNED NOT NULL,
   read_throughput BIGINT(20) SIGNED NOT NULL,
   write_throughput BIGINT(20) SIGNED NOT NULL,
   read_duration INT(10) SIGNED NOT NULL,
   write_duration INT(10) SIGNED NOT NULL,
   PRIMARY KEY (id)
) ENGINE=MyISAM DEFAULT CHARSET=latin1
"""

        logging.debug("Creating database table:\n%s", sql)

        with closing(mysql.connector.connect(host=self._host,
                                             user=self._user,
                                             password=self._password,
                                             db=self._database)) as conn:

            with closing(conn.cursor()) as cur:
                cur.execute(sql)

    def insert(self, ost_perf_result):

        if not ost_perf_result:
            raise RuntimeError('Insert failed with empty OST perf result object!')

        self._ost_perf_result_list.append(ost_perf_result)

    def store(self):

        len_ost_perf_result_list = len(self._ost_perf_result_list)

        sql = "INSERT INTO " \
            + self._table \
            + "(" \
            + "read_timestamp, " \
            + "write_timestamp, " \
            + "ost, " \
            + "size, " \
            + "read_throughput, " \
            + "write_throughput, " \
            + "read_duration, " \
            + "write_duration" \
            + ") " \
            + "VALUES "

        if len_ost_perf_result_list > 0:

            sql += "(" + self._ost_perf_result_list[0] + ")"

            if len_ost_perf_result_list > 1:

                for i in range(1, len_ost_perf_result_list):
                    sql += ",(" + self._ost_perf_result_list[i] + ")"

        logging.debug("Executing SQL statement:\n%s", sql)

        with closing(mysql.connector.connect(host=self._host,
                                             user=self._user,
                                             password=self._password,
                                             database=self._database)) as conn:

            with closing(conn.cursor()) as cur:

                cur.execute(sql)

                if cur.rowcount != len_ost_perf_result_list:
                    raise RuntimeError("Number of rows inserted is not equal to number of input records!")

        logging.debug("Inserted: %i records into table: %s", len_ost_perf_result_list, self._table)

    def count(self):
        return len(self._ost_perf_result_list)

    def clear(self):
        del self._ost_perf_result_list[:]
