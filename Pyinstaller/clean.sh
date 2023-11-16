#!/bin/bash

TARGET_DIR=pybuild

case "$1" in

	all)
		$(rm -r "$TARGET_DIR"/*)
	;;

	master)
		$(find "$TARGET_DIR" -name 'cyclone-master.*' -type f -delete)
		$(rm -r "$TARGET_DIR"/build/cyclone-master.py)
	;;

	controller)
		$(find "$TARGET_DIR" -name 'cyclone-controller.*' -type f -delete)
		$(rm -r "$TARGET_DIR"/build/cyclone-controller.py)
	;;

	database-proxy)
		$(find "$TARGET_DIR" -name 'cyclone-database-proxy.*' -type f -delete)
		$(rm -r "$TARGET_DIR"/build/cyclone-database-proxy.py)
	;;

	*)
		echo "Usage: $0 {all|master|controller|database-proxy}"
		exit 1
	;;

esac
