#!/bin/bash

/usr/bin/env python3 --version | grep -q " 3.5"
if [ "$?" != "0" ]; then
	echo "ERROR: Creating the Briefcase-based Xcode project for iOS requires Python 3.5"
	exit 1
fi

/usr/bin/env pip3 show briefcase > /dev/null
if [ "$?" != "0" ]; then
	echo "ERROR: Please install briefcase like so: pip3 install briefcase"
	exit 2
fi

/usr/bin/env pip3 show cookiecutter > /dev/null
if [ "$?" != "0" ]; then
	echo "ERROR: Please install cookiecutter like so: pip3 install cookiecutter"
	exit 3
fi

if [ -d iOS ]; then
	echo "Warning: 'iOS' directory exists. All modifications will be lost if you continue."
	echo "Continue? [y/N]?"
	read reply
	if [ "$reply" != "y" ]; then
		echo "Fair enough. Exiting..."
		exit 0
	fi
	echo "Cleaning up old iOS dir..."
	rm -fr iOS
fi

if [ -d ElectronCash/electroncash ]; then
	echo "Deleting old ElectronCash/electroncash..."
	rm -fr ElectronCash/electroncash
fi

echo "Pulling 'electroncash' libs into project from ../lib ..."
cp -fpR ../lib ElectronCash/electroncash
find ElectronCash -name \*.pyc -exec rm -f {} \; 

echo ""
echo "Building Briefcase-Based iOS Project..."
echo ""

python3.5 setup.py ios 
if [ "$?" != 0 ]; then
	echo "An error occurred running setup.py"
	exit 4
fi

cd iOS && ln -s . Support && cd .. # Fixup for broken Briefcase template.. :/

infoplist="iOS/ElectronCash/ElectronCash-Info.plist"
if [ -f "${infoplist}" ]; then
	echo ""
	echo "Adding custom keys to ${infoplist} ..."
	echo ""
	plutil -insert "NSAppTransportSecurity" -xml '<dict><key>NSAllowsArbitraryLoads</key><true/></dict>' -- ${infoplist} 
	if [ "$?" != "0" ]; then
		echo "Encountered error adding custom keys to plist!"
		exit 1
	fi
	longver=`git describe --tags`
	if [ -n "$longver" ]; then
		shortver=`echo "$longver" | cut -f 1 -d -`
		plutil -replace "CFBundleVersion" -string "$longver" -- ${infoplist} && plutil -replace "CFBundleShortVersionString" -string "$shortver" -- ${infoplist}
		if [ "$?" != "0" ]; then
			echo "Encountered error adding custom keys to plist!"
			exit 1
		fi
	fi
fi

if [ -d overrides/ ]; then
	echo ""
	echo "Applying overrides..."
	echo ""
	(cd overrides && cp -fpvR * ../iOS/ && cd ..)
fi

patches=patches/*.patch
if [ -n "$patches" ]; then
	echo ""
	echo "Applying patches..."
	echo ""
	for p in $patches; do
		patch -p 1 < $p
	done
fi

echo ''
echo '**************************************************************************'
echo '*                                                                        *'
echo '*   Operation Complete. An Xcode project has been generated in "iOS/"    *'
echo '*                                                                        *'
echo '**************************************************************************'
echo '  NOTE: Modifications to files in iOS/ will be clobbered the next    '
echo '        time this script is run.  If you intend on modifying the     '
echo '        program in Xcode, be sure to copy out modifications from iOS/ '
echo '        manually or by running ./copy_back_changes.sh.'
echo ''
