#!/bin/sh

# Usage example:
#
# dict-diff.sh Est ~/myapps/GF/lib/src/estonian/ ~/mywork/GF-Estonian/lexicons/20151114_dictest/

if [ $# -ne 3 ]
then
    echo "Usage: `basename $0` <lang> <dir1> <dir2>"
    exit
fi

lang=$1
dir1=$2
dir2=$3

echo "Frequency ranking of added categories:"
diff ${dir1}Dict${lang}Abs.gf ${dir2}Dict${lang}Abs.gf | grep "^>" | sed "s/.*://" | sort | uniq -c | sort -nr

echo "Frequency ranking of removed categories:"
diff ${dir1}Dict${lang}Abs.gf ${dir2}Dict${lang}Abs.gf | grep "^<" | sed "s/.*://" | sort | uniq -c | sort -nr
