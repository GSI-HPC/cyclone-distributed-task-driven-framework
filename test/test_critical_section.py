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


import logging
import multiprocessing
import time

from ctrl.critical_section import CriticalSection


def worker_func(wid, lock):

    logging.info("Started Worker: %s" % wid)

    # Check if critical section is locked,
    # since the timeout might interrupt the blocking wait.
    with CriticalSection(lock, timeout=1) as critical_section:

        logging.info("Lock acquired: %s" % critical_section.is_locked())

        if critical_section.is_locked():

            logging.info("Worker[%s] - locked" % wid)
            time.sleep(3)
            logging.info("Worker[%s] - released" % wid)

    return


def main():

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s")

    logging.info("START")

    mp_lock = multiprocessing.Lock()

    p1 = multiprocessing.Process(target=worker_func, args=(1, mp_lock))
    p2 = multiprocessing.Process(target=worker_func, args=(2, mp_lock))

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    logging.info("END")


if __name__ == '__main__':
    main()


