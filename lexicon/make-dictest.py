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
#   - turn synset elements into variants (e.g. in post-processing)
#   - handle verbs like "kokku kasvama"
#   - reject plural nouns: abikaasad_N (causes ambiguity as EstNLTK generates forms from the singular form)

from estnltk import analyze, synthesize
from estnltk.wordnet import wn
import sys
import re
import argparse

DEFAULT_POS_TAGS_ORDER = ['n', 'v', 'a', 'b']

pos_tags = {
    'n': wn.NOUN,
    'v': wn.VERB,
    'a': wn.ADJ,
    'b': wn.ADV
}

pos_to_gf = {
    'n': 'N',
    'v': 'V',
    'a': 'A',
    'b': 'Adv'
}


# TODO: add adt
NOUN_FORMS = ['sg n', 'sg g', 'sg p', 'sg ill', 'pl g', 'pl p']
VERB_FORMS = ['ma', 'da', 'b', 'takse', 'ge', 's', 'nud', 'tud']

# Set of words that have different forms depending on their meaning
# TODO: maybe it is possible to query EstNLTK for such words
SET_PALK = set(['palk', 'nukk'])

class Entry:

    def __init__(self, name, lemma, pos):
        self.name = name
        self.lemma = lemma
        self.pos = pos
        self.prefix, self.forms = get_forms(lemma, pos)

    def is_illegal(self):
        """Entry is illegal iff at least one form is missing.
        """
        return ('' in self.forms)

    def pp(self):
        return '{0}\t{1}\t{2}\t{3}'.format(self.pos, self.name, self.lemma, self.forms)

    def gf(self):
        pos = self.pos
        oper_args = ' '.join(['"' + x + '"' for x in self.forms])
        funname = get_funname(self.lemma, pos_to_gf.get(pos))
        if pos == 'n':
            if self.prefix:
                return '{0} = mkN "{1}" (mkN {2}) ;'.format(funname, self.prefix, oper_args)
            return '{0} = mkN {1} ;'.format(funname, oper_args)
        elif pos == 'a':
            if self.prefix:
                return '{0} = mkA (mkN "{1}" (mkN {2})) ;'.format(funname, self.prefix, oper_args)
            return '{0} = mkA (mkN {1}) ;'.format(funname, oper_args)
        elif pos == 'v':
            if self.prefix:
                return '{0} = mkV "{1}" (mkV {2}) ;'.format(funname, self.prefix, oper_args)
            return '{0} = mkV {1} ;'.format(funname, oper_args)
        return '{0} = mkAdv {1} ;'.format(funname, oper_args)

def quote_funname(name):
    """Quote funnames which contain characters other than [^_A-Za-z0-9]
    """
    if re.search(r"[^_A-Za-z0-9']", name):
        return "'" + re.sub("'", "\\'", name) + "'"
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
    for synset in wn.all_synsets(pos=pos_tags.get(pos)):
        for lemma in synset.lemmas():
            yield pos, synset.name, lemma.name

def filter_synset_lemmas(gen):
    """Filter out various unwanted lemmas, e.g. multi-word nouns.
    Multiword adjectives, adverbs and verbs are not frequent in EstWN, and do not
    have the same issues as nouns.
    """
    for pos, synset_name, lemma_name in gen:
        if '-' == lemma_name[-1]:
            print('Warning: ignored {0} entry with trailing hyphen: {1}'.format(pos, lemma_name), file=sys.stderr)
            continue
        if ' ' in lemma_name:
            # Do not generate multi-word nouns/adjectives with space (e.g. "avalik sektor", "hiljaks jäänud").
            # Nouns should be handled by the grammar to get the agreement right.
            if pos == wn.NOUN or pos == wn.ADJ:
                print('Warning: ignored {0} entry with space: {1}'.format(pos, lemma_name), file=sys.stderr)
                continue
        yield pos, synset_name, lemma_name


def merge(forms):
    """TODO: deal with the issue that there can be multiple forms for a single case
    """
    if len(forms):
        return forms[0]
    return ''

def get_forms_aux(lemma, pos, form_ids):
    """
    Notes:
    - we do not treat hyphenated words (e.g. "13-silbik") as compounds because the hyphen tends to get lost
    """
    if '-' not in lemma and (pos == 'S' or pos == 'A'):
        an_list = analyze([lemma])[0]['analysis']
        for an in an_list:
            if an['partofspeech'] == pos and len(an['root_tokens']) > 1:
                tokens = an['root_tokens']
                last_token = tokens[-1]
                if last_token not in SET_PALK:
                    return ''.join(tokens[0:-1]), [merge(synthesize(last_token, form, pos)) for form in form_ids]
    return '', [merge(synthesize(lemma, form, pos)) for form in form_ids]

def get_forms(lemma, pos=wn.NOUN):
    """Get the relevant forms given the lemma and its POS.
    Note that synthesize also handles compounding and is smart
    about words like 'kuupalk' (gen: 'palga') and 'kantpalk' (gen: 'palgi').
    If the input lemma contains spaces then we synthesize based on the last part.
    (In the previous approaches we did compounding separately and
    applied form generation only to the last element of the compound.)
    """
    parts = lemma.split(' ')
    prefix1 = ' '.join(parts[0:-1])
    if pos == wn.NOUN or pos == 'n':
        prefix2, forms = get_forms_aux(parts[-1], 'S', NOUN_FORMS)
    elif pos == wn.ADJ or pos == 'a':
        prefix2, forms = get_forms_aux(parts[-1], 'A', NOUN_FORMS)
    elif pos == wn.ADV or pos == 'b':
        prefix2, forms = '', [lemma]
    else:
        # TODO: do not split in case of verbs?
        prefix2, forms = get_forms_aux(parts[-1], 'V', VERB_FORMS)
    if prefix1:
        return prefix1 + ' ' + prefix2, forms
    if prefix2:
        return prefix2, forms
    return '', forms

def get_args():
    csl = lambda s: [el.strip() for el in s.split(',')]
    p = argparse.ArgumentParser(description='Generates a GF monolingual lexicon DictEst based in the Estonian WordNet and the morphology tools that are embedded in EstNLTK')
    p.add_argument('--pos-tags', type=csl, action='store', dest='pos_tags', default=DEFAULT_POS_TAGS_ORDER)
    p.add_argument('-v', '--version', action='version', version='%(prog)s v0.1.1')
    return p.parse_args()


def main():
    args = get_args()
    for pos in args.pos_tags:
        for pos_name, synset_name, lemma_name in filter_synset_lemmas(gen_wn_lemmas(pos)):
            entry = Entry(synset_name, lemma_name, pos_name)
            if entry.is_illegal():
                print('Warning: ignored entry with empty form: ' + entry.pp(), file=sys.stderr)
            else:
                print('{0}\t{1}\t{2}'.format(synset_name, lemma_name, entry.gf()))

if __name__ == '__main__':
    main()
