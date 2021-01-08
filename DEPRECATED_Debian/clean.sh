#!/bin/bash


MAS_DIR=lfsm-master
CON_DIR=lfsm-controller
DBP_DIR=lfsm-database-proxy

function clean_deb_package {

	rm "$1"*.buildinfo
	rm "$1"*.changes
	rm "$1"*.deb
	rm "$1"/debian/*debhelper*
	rm "$1"/debian/*substvars
	rm "$1"/debian/files
	rm -r "$1"/debian/"$1"
}

case "$1" in

	all)
		clean_deb_package "$MAS_DIR"
		clean_deb_package "$CON_DIR"
		clean_deb_package "$DBP_DIR"
	;;

	master)
		clean_deb_package "$MAS_DIR"
	;;

	controller)
		clean_deb_package "$CON_DIR"
	;;

	database-proxy)
		clean_deb_package "$DBP_DIR"
	;;

	*)
		echo "Usage: $0 {all|master|controller|database-proxy}"
		exit 1
	;;

esac
