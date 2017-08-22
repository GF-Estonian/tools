#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# WORK IN PROGRESS
#
# Converts the EstNLTK Estonian WordNet resource into the GF DictEst.gf lexicon.
#
# Usage (runtime ~2 min):
#
#   make-dictest.py > out.tsv
#   make-dictest.py --pos-tags=n | cut -f2,3 | sort | uniq > nouns.tsv 2> nouns.err
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

from estnltk import synthesize
from estnltk.wordnet import wn
import sys
import re
import argparse

DEFAULT_POS_TAGS_ORDER=['n', 'v', 'a', 'b']

pos_tags = {
    'n': wn.NOUN,
    'v': wn.VERB,
    'a': wn.ADJ,
    'b': wn.ADV
}


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

def quote_funname(name):
    """
    Quote funnames which contain characters other than [^_A-Za-z0-9]
    """
    if not re.search(r'[\']', name) and re.search(r'[^_A-Za-z0-9]', name):
        return "'" + name + "'"
    return name

def get_funname(word, pos=None):
    word = re.sub(r' ', '_', word)
    if pos is None:
        return quote_funname(word)
    return quote_funname(word + '_' + pos)

def gen_wn_lemmas(pos):
    """Generates POS-tag, synset ID, lemma.
    That is all the info that we currently want from WordNet.
    TODO: get ILI links too to be able to make bilingual lexicons.
    """
    wnpos = pos_tags.get(pos)
    for synset in wn.all_synsets(pos=wnpos):
        for lemma in synset.lemmas():
            yield pos, synset.name, lemma.name


def merge(forms):
    """TODO: deal with the issue that there can be multiple forms for a single case
    """
    if len(forms):
        return forms[0]
    return ''

def combine(lst, el):
    if len(el):
        return ' '.join(lst + [el])
    return ''

def get_forms_aux(lemma, pos, form_ids):
    return [ merge(synthesize(lemma, form, pos)) for form in form_ids ]

def get_forms(lemma, pos=wn.NOUN):
    """Get the relevant forms given the lemma and its POS.
    Note that synthesize also handles compounding and is smart
    about words like 'kuupalk'.
    If the input lemma contains spaces then we synthesize based on the last part.
    (In the previous approaches we did compounding separately and
    applied form generation only to the last element of the compound.)
    """
    parts = lemma.split(' ')
    if pos == wn.NOUN or pos == 'n':
        return [ combine(parts[0:-1], x) for x in get_forms_aux(parts[-1], 'S', NOUN_FORMS) ]
    elif pos == wn.ADJ or pos == 'a':
        return [ combine(parts[0:-1], x) for x in get_forms_aux(parts[-1], 'S', NOUN_FORMS) ]
    elif pos == wn.ADV or pos == 'b':
        return [ lemma ]
    else:
        return [ combine(parts[0:-1], x) for x in get_forms_aux(parts[-1], 'V', VERB_FORMS) ]


def get_args():
    csl = lambda s: [el.strip() for el in s.split(',')]
    p = argparse.ArgumentParser(description='Convert the Estonian WordNet into a GF monolingual lexicon DictEst')
    p.add_argument('--pos-tags', type=csl, action='store', dest='pos_tags', default=DEFAULT_POS_TAGS_ORDER)
    p.add_argument('-v', '--version', action='version', version='%(prog)s v0.1.1')
    return p.parse_args()


def main():
    args = get_args()
    for pos in args.pos_tags:
        for pos_name, synset_name, lemma_name in gen_wn_lemmas(pos):
            entry = Entry(synset_name, lemma_name, pos_name)
            if entry.is_illegal():
                print('Warning: ignored entry with empty form: ' + entry.pp(), file=sys.stderr)
            else:
                print('{0}\t{1}\t{2}'.format(synset_name, lemma_name, entry.gf()))

if __name__ == '__main__':
    main()
