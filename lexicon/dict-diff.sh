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

diff1=`mktemp`
diff2=`mktemp`

echo $lang
echo $dir1
echo $dir2
echo "Frequency ranking of added categories:"
diff ${dir1}Dict${lang}Abs.gf ${dir2}Dict${lang}Abs.gf > $diff1

cat $diff1 | grep "^>" | sed "s/.*://" | sort | uniq -c | sort -nr

echo "Frequency ranking of removed categories:"
cat $diff1 | grep "^<" | sed "s/.*://" | sort | uniq -c | sort -nr

diff ${dir1}Dict${lang}.gf ${dir2}Dict${lang}.gf > $diff2
echo "Added lines"
cat $diff2 | grep "^>" | wc -l

echo "Removed lines"
cat $diff2 | grep "^<" | wc -l

echo "Number of chars/lines"
wc ${dir1}Dict${lang}Abs.gf ${dir2}Dict${lang}Abs.gf ${dir1}Dict${lang}.gf ${dir2}Dict${lang}.gf
