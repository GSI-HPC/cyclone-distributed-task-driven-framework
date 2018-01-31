#!/bin/bash

MAS_DIR=lfsm-master
CON_DIR=lfsm-controller
DBP_DIR=lfsm-database-proxy

function build_deb_package {

	cd "$1"

	dpkg-buildpackage -us -uc -b

	cd - 1>/dev/null
}

case "$1" in

	all)
		build_deb_package "$MAS_DIR"
		build_deb_package "$CON_DIR"
		build_deb_package "$DBP_DIR"
	;;

	master)
		build_deb_package "$MAS_DIR"
	;;

	controller)
		build_deb_package "$CON_DIR"
	;;

	database-proxy)
		build_deb_package "$DBP_DIR"
	;;

	*)
		echo "Usage: $0 {all|master|controller|database-proxy}"
		exit 1
	;;

esac
