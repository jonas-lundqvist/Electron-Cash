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
cd iOS && ln -s . Support # Fixup for broken Briefcase template.. :/


