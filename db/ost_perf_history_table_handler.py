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

        self.host = host
        self.user = user
        self.passwd = passwd
        self.db = db
        self.table_name = table_name

    def create_table(self):

        with closing(MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.db)) as conn:
            with closing(conn.cursor()) as cur:

                sql = """
CREATE TABLE """ + self.table_name + """ (
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
                cur.execute(sql)


