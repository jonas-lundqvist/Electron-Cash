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
c=`find ElectronCash/electroncash -type f -name \*.py -print`
popd > /dev/null

allYes=0
ct=0
skipped=0

function doIt() {
    f1=$1
    f2=$2
    dstInfo=$3

   	if diff -q $f1 $f2 > /dev/null 2>&1; then
		true
	else
        while true; do
            answer=""
            prompt="$f1 changed -- copy back to $dstInfo ? ([y]es/[n]/[a]ll/[d]iff)"
            if [ "$allYes" != "1" ]; then
            	echo "$prompt"
            fi
        	if [ "$allYes" == "0" ]; then
    			read answer
    		fi
            if [ "$answer" == "d" ]; then
                diff -u $f1 $f2 | less
                echo ""
                continue
            fi
            break
        done
		if [ "$answer" == "a" ]; then 
			allYes=1
		fi
		if [ "$answer" == "y" -o "$allYes" == "1" ]; then
			cp -v $f1 $f2
			let ct++
        else
            let skipped++
		fi
	fi
}

for file in $a $b; do
    f1="${projdir}/${file}"
    f2="${file}"
    doIt "$f1" "$f2" "ElectronCash/"
done

for f in $c; do
    file=`echo $f | cut -f 3- -d '/'`
    f1="${projdir}/${f}"
    f2="../lib/${file}"
    doIt "$f1" "$f2" "../lib/"
done


echo ""

if ((ct>0)); then
	echo "Copied back $ct changed file(s)" 
fi

if ((skipped>0)); then
    echo "Skipped $skipped"
fi

if [ $skipped == 0 -a $ct == 0 ]; then
    echo "No changes detected in iOS/"
fi

echo "Done."

