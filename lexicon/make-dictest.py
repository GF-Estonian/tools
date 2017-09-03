#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Converts the EstNLTK Estonian WordNet resource into the GF DictEst.gf lexicon,
# using morphological analysis and synthesis provided by EstNLTK.
#
# Usage (runtime ~2 min):
#
#   make-dictest.py > out.tsv
#   make-dictest.py --pos-tags=n | cut -f2,3 | sort | uniq > nouns.tsv 2> nouns.err
#
# Output example (3 columns: synset ID, lemma, and GF lexicon entry):
#
# fortuuna.n.01 <HT> fortuuna <HT> fortuuna_N = mkN "fortuuna" "fortuuna" "fortuunat" "fortuunasse" "fortuunade" "fortuunasid" ;
# fortuuna.n.01 <HT> sanss <HT> sanss_N = mkN "sanss" "sansi" "sanssi" "sansisse" "sansside" "sansse" ;
# fortuuna.n.01 <HT> õnn <HT> 'õnn_N' = mkN "õnn" "õnne" "õnne" "õnnesse" "õnnede" "õnni" ;
# küünarnukk.n.01 <HT> küünarnukk <HT> 'küünarnukk_N' = mkN "küünarnukk" "küünarnuki" "küünarnukki" "küünarnukisse" "küünarnukkide" "küünarnukke" ;
# küünarnukk.n.01 <HT> küünarpea <HT> 'küünarpea_N' = mkN "küünar" (mkN "pea" "pea" "pead" "peasse" "peade" "päid") ;
#
# Notes:
# - multi-words units with spaces are generally not generated as these should be handled by the grammar
#   (e.g. "avalik sektor" should not be represented as a multi-word noun because then we won't get the
#   form "avaliku sektori")
# - lemma must match the 1st form. This avoids incorrect entries like: inimesed_N = mkN "inimene" ...
# - we generally represent compounds using "mkN + mkN", unless the last part of the compound has
#   multiple forms in nominative and genitive (e.g. "palk", "nukk", "maks", "kott").
#   Because the synthesizer can handle compounding and is smart about such words, we let it generate forms
#   from the compound, e.g. kuupalk->kuupalga, kantpalk->kantpalgi
# - we do not treat hyphenated words (e.g. "13-silbik") as compounds because the hyphen tends to get lost during analysis
#
# TODO:
# - maybe (optionally) turn synset elements into variants (e.g. in post-processing)
# - deal with cases where multiple forms are generated (palk -> palga, palgi)
# - test this script also on verbs
# - handle words like "Kaljukits" which are both S and H in Vabamorf
# - get ILI links WordNet to be able to make bilingual lexicons

import sys
import re
import argparse
from estnltk import synthesize, Text
from estnltk.wordnet import wn

DEFAULT_POS_TAGS_ORDER = ['n', 'v', 'a', 'b']

POS_TO_WN = {
    'n': wn.NOUN,
    'v': wn.VERB,
    'a': wn.ADJ,
    'b': wn.ADV
}

POS_TO_GF = {
    'n': 'N',
    'v': 'V',
    'a': 'A',
    'b': 'Adv'
}


# TODO: add adt
NOUN_FORMS = ['sg n', 'sg g', 'sg p', 'sg ill', 'pl g', 'pl p']
VERB_FORMS = ['ma', 'da', 'b', 'takse', 'ge', 's', 'nud', 'tud']

class Entry:
    """Lexicon entry"""

    def __init__(self, name, lemma, pos):
        """Init"""
        self.name = name
        self.lemma = lemma
        self.pos = pos
        self.prefix, self.forms = get_forms(lemma, pos)

    def is_illegal(self):
        """Entry is illegal iff at least one form is missing.
        """
        return len(self.forms) == 0 or ('' in self.forms)

    def as_pp(self):
        """Pretty-printer"""
        return '{0}, {1}, {2}, "{3}", {4}'.format(self.pos, self.name, self.lemma, self.prefix, self.forms)

    def as_gf(self):
        """Make GF lexicon entry"""
        pos = self.pos
        oper_args = ' '.join(['"' + x + '"' for x in self.forms])
        funname = get_funname(self.lemma, POS_TO_GF.get(pos))
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
    """Quote operator name that contain characters other than [^_A-Za-z0-9']
    """
    if re.search(r"[^_A-Za-z0-9']", name):
        return "'" + re.sub("'", "\\'", name) + "'"
    return name

def get_funname(word, pos=None):
    """Make GF operator name"""
    word = re.sub(r' ', '_', word)
    if pos is None:
        return quote_funname(word)
    return quote_funname(word + '_' + pos)

def gen_wn_lemmas(pos):
    """Generates POS-tag, synset ID, lemma.
    That is all the info that we currently want from WordNet.
    """
    for synset in wn.all_synsets(pos=POS_TO_WN.get(pos)):
        for lemma in synset.lemmas():
            yield pos, synset.name, lemma.name

def filter_synset_lemmas(gen):
    """Filter out various unwanted lemmas, e.g. multi-word nouns.
    Multiword adjectives, adverbs and verbs are not frequent in EstWN, and do not
    have the same issues as nouns.
    """
    for pos, synset_name, lemma_name in gen:
        if lemma_name[-1] == '-':
            print('Warning: ignored {0} entry with trailing hyphen: {1}'.format(pos, lemma_name), file=sys.stderr)
            continue
        if ' ' in lemma_name:
            # Do not generate multi-word nouns/adjectives with space (e.g. "avalik sektor", "hiljaks jäänud").
            # Nouns should be handled by the grammar to get the agreement right.
            if pos == wn.NOUN or pos == wn.ADJ:
                print('Warning: ignored {0} entry with space: {1}'.format(pos, lemma_name), file=sys.stderr)
                continue
        yield pos, synset_name, lemma_name


def take_first(forms):
    """Takes the first form.
    """
    if forms:
        return forms[0]
    return ''

def synth(lemma, pos, form_ids):
    """
    Do not allow entries where the lemma differs from the first form
    e.g. inimesed_N = mkN "inimene" ...
    """
    forms1 = synthesize(lemma, form_ids[0], pos)
    if lemma == take_first(forms1):
        yield forms1
    else:
        return
    for form_id in form_ids[1:]:
        yield synthesize(lemma, form_id, pos)

def get_forms_aux(lemma, pos, form_ids):
    """Applies cmpound splitting to nouns and adjectives to generate a more
    compact GF representation. However, we avoid calculating forms
    from the last part of the compound if multiple forms are possible, e.g.
    we generate forms from "kuupalk" instead of "palk".
    """
    if '-' not in lemma and (pos == 'S' or pos == 'A'):
        an_list = Text(lemma, disambiguate=False, propername=False).analysis[0]
        for an_item in an_list:
            if an_item['partofspeech'] == pos and an_item['form'] == 'sg n' and len(an_item['root_tokens']) > 1:
                tokens = an_item['root_tokens']
                last_token = tokens[-1]
                forms_list = list(synth(last_token, pos, form_ids))
                # We require that there is a single form for nominative and genitive
                if all(len(forms) == 1 for forms in forms_list[0:2]):
                    return ''.join(tokens[0:-1]), [take_first(form) for form in forms_list]
    return '', list([take_first(form) for form in synth(lemma, pos, form_ids)])


def get_forms(lemma, pos=wn.NOUN):
    """Get the relevant forms given the lemma and its POS.
    """
    if pos == wn.ADV or pos == 'b':
        return '', [lemma]

    parts = lemma.split(' ')
    prefix1 = ' '.join(parts[0:-1])
    last_part = parts[-1]
    if pos == wn.NOUN or pos == 'n':
        prefix2, forms = get_forms_aux(last_part, 'S', NOUN_FORMS)
    elif pos == wn.ADJ or pos == 'a':
        prefix2, forms = get_forms_aux(last_part, 'A', NOUN_FORMS)
    else:
        prefix2, forms = get_forms_aux(last_part, 'V', VERB_FORMS)
    if prefix1:
        return prefix1 + ' ' + prefix2, forms
    if prefix2:
        return prefix2, forms
    return '', forms


def get_args():
    """Returns command line arguments"""
    csl = lambda s: [el.strip() for el in s.split(',')]
    parser = argparse.ArgumentParser(description='Generates a GF monolingual lexicon DictEst based on the Estonian WordNet and the morphology tools that are embedded in EstNLTK')
    parser.add_argument('--pos-tags', type=csl, action='store', dest='pos_tags', default=DEFAULT_POS_TAGS_ORDER)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s v0.2.0')
    return parser.parse_args()


def main():
    """Main"""
    args = get_args()
    for pos in args.pos_tags:
        for pos_name, synset_name, lemma_name in filter_synset_lemmas(gen_wn_lemmas(pos)):
            entry = Entry(synset_name, lemma_name, pos_name)
            if entry.is_illegal():
                print('Warning: ignored entry with empty form: ' + entry.as_pp(), file=sys.stderr)
            else:
                print('{0}\t{1}\t{2}'.format(synset_name, lemma_name, entry.as_gf()))

if __name__ == '__main__':
    main()
