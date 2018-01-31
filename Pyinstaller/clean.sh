#!/bin/bash


TARGET_DIR=pybuild

case "$1" in

	all)
		$(rm -r "$TARGET_DIR"/*)
	;;

	master)
		$(find "$TARGET_DIR" -name 'lfsm-master.*' -type f -delete)
		$(rm -r "$TARGET_DIR"/build/lfsm-master.py)
	;;

	controller)
		$(find "$TARGET_DIR" -name 'lfsm-controller.*' -type f -delete)
		$(rm -r "$TARGET_DIR"/build/lfsm-controller.py)
	;;

	database-proxy)
		$(find "$TARGET_DIR" -name 'lfsm-database-proxy.*' -type f -delete)
		$(rm -r "$TARGET_DIR"/build/lfsm-database-proxy.py)
	;;

	*)
		echo "Usage: $0 {all|master|controller|database-proxy}"
		exit 1
	;;

esac
