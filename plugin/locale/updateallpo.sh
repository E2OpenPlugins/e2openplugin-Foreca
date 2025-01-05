#!/bin/bash
# Script to generate po files outside of the normal build process
#  
# Pre-requisite:
# The following tools must be installed on your system and accessible from path
# gawk, find, xgettext, sed, python, msguniq, msgmerge, msgattrib, msgfmt, msginit
#
# Run this script from within the locale folder.
#
# Author: Pr2
# Version: 1.0
#
#
# On Mac OSX find option are specific
#
findoptions=""
if [[ "$OSTYPE" == "darwin"* ]]
	then
		# Mac OSX
		printf "Script running on Mac OSX [%s]\n" "$OSTYPE"
    	findoptions="-s -X"
fi
#
# sed detection
#
localgsed="sed"
gsed --version 2> /dev/null | grep -q "GNU"
if [ $? -eq 0 ]; then
        localgsed="gsed"
else
        "$localgsed" --version | grep -q "GNU"
        if [ $? -eq 0 ]; then
                printf "GNU sed found: [%s]\n" $localgsed
        fi
fi
Plugin=Foreca
FilePath=/LC_MESSAGES/
printf "Po files update/creation from script starting.\n"
languages=($(ls -d ./*/ | $localgsed 's/\/$//g; s/.*\///g'))
#
# On Mac OSX find option are specific
#
findoptions=""
if [[ "$OSTYPE" == "darwin"* ]]
	then
		# Mac OSX
		printf "Script running on Mac OSX [%s]\n" "$OSTYPE"
    	findoptions="-s -X"
fi
#
# sed detection
#
localgsed="sed"
gsed --version 2> /dev/null | grep -q "GNU"
if [ $? -eq 0 ]; then
        localgsed="gsed"
else
        "$localgsed" --version | grep -q "GNU"
        if [ $? -eq 0 ]; then
                printf "GNU sed found: [%s]\n" $localgsed
        fi
fi
#
# Arguments to generate the pot and po files are not retrieved from the Makefile.
# So if parameters are changed in Makefile please report the same changes in this script.
#

printf "Creating temporary file $Plugin-py.pot\n"
find $findoptions .. -name "*.py" -exec xgettext --no-wrap -L Python --from-code=UTF-8 -kpgettext:1c,2 --add-comments="TRANSLATORS:" -d $Plugin -s -o $Plugin-py.pot {} \+
$localgsed --in-place $Plugin-py.pot --expression=s/CHARSET/UTF-8/
printf "Creating temporary file $Plugin-xml.pot\n"
find $findoptions .. -name "*.xml" -exec python3 xml2po.py {} \+ > $Plugin-xml.pot
printf "Merging pot files to create: $Plugin.pot\n"
cat $Plugin-py.pot $Plugin-xml.pot | msguniq --no-wrap -o $Plugin.pot -
OLDIFS=$IFS
IFS=" "
printf "\n"; read -n1 -r -p "Press 'M' to continue with generating .mo files" key; printf "\n"
for lang in "${languages[@]}" ; do
	if [ -f $lang$FilePath$Plugin.po ]; then 
		printf "Updating existing translation file %s.po\n" $lang
		msgmerge --backup=none --no-wrap -s -U $lang$FilePath$Plugin.po $Plugin.pot && touch $lang$FilePath$Plugin.po
		msgattrib --no-wrap --no-obsolete $lang$FilePath$Plugin.po -o $lang$FilePath$Plugin.po
		if [ "$key" = 'M' ]; then
			msgfmt -o $lang$FilePath$Plugin.mo $lang$FilePath$Plugin.po
		fi
	else
		if [ ! -d $lang$FilePath ]; then
			mkdir $lang$FilePath
		fi
		printf "New file created: %s, please add it to github before commit\n" $lang$FilePath$Plugin.po
		msginit -l $lang$FilePath$Plugin.po -o $lang$FilePath$Plugin.po -i $Plugin.pot --no-translator
		if [ "$key" = 'M' ]; then
			msgfmt -o $lang$FilePath$Plugin.mo $lang$FilePath$Plugin.po
		fi
	fi
done
rm $Plugin-py.pot $Plugin-xml.pot
IFS=$OLDIFS
printf "Po files update/creation from script finished!\n"


