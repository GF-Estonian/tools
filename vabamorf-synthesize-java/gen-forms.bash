
nouns="nouns.6forms.csv"
adj="adj.6forms.csv"
verbs="verbs.8forms.csv"

time cat ${GF_EST_SRC}/data/$nouns | sed "s/,.*//" | tr '|' '\012' | uniq | java Synthesize S | grep -v ", ," > $nouns
time cat ${GF_EST_SRC}/data/$adj | sed "s/,.*//" | tr '|' '\012' | uniq | java Synthesize A | grep -v ", ," > $adj
time cat ${GF_EST_SRC}/data/$verbs | sed "s/,.*//" | tr '|' '\012' | uniq | java Synthesize V | grep -v ", ," > $verbs
