#!/bin/bash

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


