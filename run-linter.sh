#!/bin/bash
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

CMD_FIND=`which find`
CMD_XARGS=`which xargs`
CMD_PYLINT=`which pylint`

OUTPUT_LINTER="$PWD/linter.out"

function logInfo {
    echo "INFO - $1"
}

function logFatal {
    echo "ERROR - $1"
    exit 1
}

function checkDependencies {
    logInfo "Checking dependencies..."

    cmd_list=("find" $CMD_FIND "xargs" $CMD_XARGS "linter" $CMD_PYLINT)
    len_list=${#cmd_list[@]}

    for (( i=0; i<$len_list; i+=2 ));
    do
        cmd_name="${cmd_list[$i]}"
        cmd_bin="${cmd_list[$i+1]}"

        if [ -f "$cmd_bin" ]; then
            logInfo "$cmd_name command found: $cmd_bin"
        else
            logFatal "$cmd_name command not found: $cmd_bin"
        fi
    done

    logInfo "All dependencies OK"
}

function runLinter {
    logInfo "Started code linting..."
    # pylint cannot handle '.' for current directory, so all files are passed.
    # See issue: https://github.com/PyCQA/pylint/issues/352
    ($CMD_FIND . -name "*.py" | $CMD_XARGS -I {} $CMD_PYLINT {}) > $OUTPUT_LINTER
    logInfo "Output written to $OUTPUT_LINTER"
    logInfo "Finished code linting"

}

checkDependencies
runLinter
