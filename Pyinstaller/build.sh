#!/bin/bash

TARGET_DIR=pybuild
SOURCE_DIR=../../

# Use pyinstaller default paths:
# --distpath=.dist
# --workpath=.build

MASTER_EXE=dist/lfsm-master.py
CONTROLLER_EXE=dist/lfsm-controller.py
DATABASE_PROXY_EXE=dist/lfsm-database-proxy.py

# !!! Build successfully tested with -> Python version 3.6.8 and 3.8.2 !!!
HIDDEN_IMPORTS="--hidden-import task.ost_migrate_task \
                --hidden-import task.empty_task \
                --hidden-import task.io_task \
                --hidden-import task.alert_io_task \
                --hidden-import task.generator.lustre_ost_file_migration_task_generator"

function build_master {

	$(pyinstaller --onefile $HIDDEN_IMPORTS --name lfsm-master.py $SOURCE_DIR/lfsm\_master.py)

	if [ -f "$MASTER_EXE" ]; then
		echo ">>> Python executable found under: $MASTER_EXE"
	else
		echo ">>> Python executable not found under: $MASTER_EXE"
	fi

}

function build_controller {

	$(pyinstaller --onefile $HIDDEN_IMPORTS --name lfsm-controller.py $SOURCE_DIR/lfsm_controller.py)

	if [ -f "$CONTROLLER_EXE" ]; then
		echo ">>> Python executable found under: $CONTROLLER_EXE"
	else
		echo ">>> Python executable not found under: $CONTROLLER_EXE"
	fi

}

function build_database_proxy {

	$(pyinstaller --onefile --name lfsm-database-proxy.py $SOURCE_DIR/lfsm\_database\_proxy.py)

	if [ -f "$DATABASE_PROXY_EXE" ]; then
		echo ">>> Python executable found under: $DATABASE_PROXY_EXE"
	else
		echo ">>> Python executable not found under: $DATABASE_PROXY_EXE"
	fi

}

case "$1" in

	all)

		mkdir -p "$TARGET_DIR"
		cd "$TARGET_DIR"

		build_master
		build_controller
		build_database_proxy

		cd - 1>/dev/null

	;;

	master)

	mkdir -p "$TARGET_DIR"
	cd "$TARGET_DIR"

	build_master

	cd - 1>/dev/null

	;;

	controller)

	mkdir -p "$TARGET_DIR"
	cd "$TARGET_DIR"

	build_controller

	cd - 1>/dev/null

	;;

	database-proxy)

	mkdir -p "$TARGET_DIR"
	cd "$TARGET_DIR"

	build_database_proxy

	cd - 1>/dev/null

	;;

	*)
		echo "Usage: $0 {all|master|controller|database-proxy}"
		exit 1
	;;

esac
