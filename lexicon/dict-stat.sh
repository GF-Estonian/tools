#!/bin/sh

# Usage example:
#
# dict-stat.sh Est ~/mywork/GF-Estonian/lexicons/20151114_dictest/
# dict-stat.sh Est ~/myapps/GF/lib/src/estonian/

if [ $# -ne 2 ]
then
    echo "Usage: `basename $0` <lang> <dir>"
    exit
fi

lang=$1
dir=$2

gf=${dir}Dict${lang}.gf

echo $lang
echo $dir
echo "Number of lexicon entries:"
cat $gf | grep " = mk" | wc -l

echo "Frequency ranking of oper patterns:"
cat $gf | grep " = mk" | sed "s/.*= //" | sed 's/"[^"]*"//g' | sed "s/  */ /g" | sed "s/;//" | sort | uniq -c | sort -nr
