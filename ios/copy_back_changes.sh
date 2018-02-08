#!/bin/bash

if [ ! -d iOS ]; then
	echo "Error: No iOS directory"
	exit 1
fi

pushd . > /dev/null
projdir="iOS/app"
cd $projdir

a=ElectronCash/*.py
b=`find ElectronCash/electroncash_gui -type f -name \*.py -print`

popd > /dev/null

allYes=0
ct=0
for file in $a $b; do
	dn=`dirname $file`
	bn=`basename $file`
	if diff -q "$projdir/$file" "$file" > /dev/null 2>&1; then
		true
	else
		answer=""
		prompt="$projdir/${file}$extra changed -- copy back to ElectronCash/ ? ([y]es/[n]/[a]ll)"
		if [ "$allYes" != "1" ]; then
			echo "$prompt"
		fi
		if [ "$allYes" == "0" ]; then
			read answer
		fi
		if [ "$answer" == "a" ]; then 
			allYes=1
		fi
		if [ "$answer" == "y" -o "$allYes" == "1" ]; then
			cp -v $projdir/$file $file
			let ct=ct+1
		fi
	fi
done

echo ""
if ((ct>0)); then
	echo "Copied back $ct changed file(s), done." 
else
	echo "No files were changed in iOS/"
fi

