#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# WORK IN PROGRESS
#
# Converts the EstNLTK Estonian WordNet resource into the GF DictEst.gf lexicon.
#
# Usage (runtime ~2 min):
#
#   ./make-dictest.py > out.tsv
#
# Output example (2 columns: synset ID and GF lexicon entry):
#
#   fortuuna.n.01   fortuuna_N = mkN "fortuuna" "fortuuna" "fortuunat" "fortuunasse" "fortuunade" "fortuunasid" ;
#   fortuuna.n.01   sanss_N = mkN "sanss" "sansi" "sanssi" "sansisse" "sansside" "sansse" ;
#   fortuuna.n.01   'õnn_N' = mkN "õnn" "õnne" "õnne" "õnnesse" "õnnede" "õnni" ;
#   jõud.n.01   'jõud_N' = mkN "jõud" "jõu" "jõudu" "jõusse" "jõudude" "jõude" ;
#   jõud.n.01   'vägi_N' = mkN "vägi" "väe" "väge" "väesse" "vägede" "vägesid
#
# TODO:
#   - if synthesize fails then try to split the word and apply synthesize on the last part
#   - exclude adjectives with hyphens
#   - turn synset elements into variants (e.g. in post-processing)

from __future__ import division, unicode_literals, print_function

from estnltk import synthesize
from estnltk.wordnet import wn
import sys
import re
import argparse

pos_tags = set([wn.NOUN, wn.VERB, wn.ADJ, wn.ADV])

# TODO: add adt
NOUN_FORMS = ['sg n', 'sg g', 'sg p', 'sg ill', 'pl g', 'pl p']
VERB_FORMS = ['ma', 'da', 'b', 'takse', 'ge', 's', 'nud', 'tud']

class Entry:

    def __init__(self, name, lemma, pos):
        self.name = name
        self.lemma = lemma
        self.pos = pos
        self.forms = get_forms(lemma, pos)

    def is_illegal(self):
        """Entry is illegal iff at least one form is missing.
        """
        return ('' in self.forms)

    def pp(self):
        return '{0}\t{1}\t{2}\t{3}'.format(self.pos, self.name, self.lemma, self.forms)

    def gf(self):
        pos = self.pos
        oper_args = ' '.join(['"' + x + '"' for x in self.forms])
        if pos == wn.NOUN or pos == 'n':
            funname = get_funname(self.lemma, 'N')
            return '{0} = mkN {1} ;'.format(funname, oper_args)
        elif pos == wn.ADJ or pos == 'a':
            funname = get_funname(self.lemma, 'A')
            return '{0} = mkA (mkN {1}) ;'.format(funname, oper_args)
        elif pos == wn.ADV or pos == 'b':
            funname = get_funname(self.lemma, 'Adv')
            return '{0} = mkAdv {1} ;'.format(funname, oper_args)
        else:
            funname = get_funname(self.lemma, 'V')
            return '{0} = mkV {1} ;'.format(funname, oper_args)


def print_utf8(s, file=sys.stdout):
    print(s.encode('utf8'), file=file)

def unicode_to_gfcode(u):
    u1 = u.decode("utf8")
    u2 = u1.encode('ascii', 'xmlcharrefreplace')
    u3 = re.sub(r'[^A-Za-z0-9\']', '_', u2)
    return u3

def quote_funname(name):
    """
    Quote funnames which contain characters other than [^_A-Za-z0-9]
    """
    if not re.search(r'[\']', name) and re.search(r'[^_A-Za-z0-9]', name):
        return "'" + name + "'"
    return unicode_to_gfcode(name)

def get_funname(word, pos=None):
    word = re.sub(r' ', '_', word)
    if pos is None:
        return quote_funname(word)
    return quote_funname(word + '_' + pos)

def gen_wn_lemmas(pos=wn.NOUN):
    """Generates POS-tag, synset ID, lemma.
    That is all the info that we currently want from WordNet.
    TODO: get ILI links too to be able to make bilingual lexicons.
    """
    for synset in wn.all_synsets(pos=pos):
        for lemma in synset.lemmas():
            yield pos, synset.name, lemma.name


def gen_wn_lemmas_from_stdin(pos=wn.NOUN):
    """Just for convenience
    """
    for raw_line in sys.stdin:
        line = raw_line.decode('utf8')
        line = line.strip()
        f = line.split('\t')
        yield f[0],f[1],f[2]


def merge(forms):
    """TODO: deal with the issue that there can be multiple forms for a single case
    """
    if len(forms):
        return forms[0]
    return ''


def get_forms(lemma, pos=wn.NOUN):
    """Get the relevant forms given the lemma and its POS.
    Note that synthesize also handles compounding and is smart
    about words like 'kuupalk'.
    (In the previous approaches we did compounding separately and
    applied form generation only to the last element of the compound.)
    """
    if pos == wn.NOUN or pos == 'n':
        return [ merge(synthesize(lemma, form, 'S')) for form in NOUN_FORMS ]
    elif pos == wn.ADJ or pos == 'a':
        return [ merge(synthesize(lemma, form, 'S')) for form in NOUN_FORMS ]
    elif pos == wn.ADV or pos == 'b':
        return [ lemma ]
    else:
        return [ merge(synthesize(lemma, form, 'V')) for form in VERB_FORMS ]


def get_args():
    p = argparse.ArgumentParser(description='Convert the Estonian WordNet into a GF monolingual lexicon DictEst')
    p.add_argument('-v', '--version', action='version', version='%(prog)s v0.0.1')
    return p.parse_args()


def main():
    args = get_args()
    for pos in pos_tags:
        for pos_name,synset_name,lemma_name in gen_wn_lemmas(pos):
            entry = Entry(synset_name, lemma_name, pos_name)
            if entry.is_illegal():
                print_utf8('Warning: ignored: ' + entry.pp(), file=sys.stderr)
            else:
                print_utf8('{0}\t{1}'.format(synset_name, entry.gf()))

if __name__ == "__main__":
    main()
