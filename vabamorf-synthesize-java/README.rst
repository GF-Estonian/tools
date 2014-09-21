vabamorf-synthesize-java
========================

Uses Vabamorf (https://github.com/Filosoft/vabamorf) to synthesize noun (adjective, propername) and verb forms
from the given lemma forms.

Build
-----

Compile the Java files in this directory

   ::

       javac -d . *.java
       jar cvfm vabamorf-synthesize.jar manifest.txt Synthesize.class ee


Run
---

1. Build ``liblinguistic_jni.so`` as explained in https://github.com/Filosoft/vabamorf/blob/master/apps/cmdline/java/readme.html

2. Place ``liblinguistic_jni.so`` to ``LD_LIBRARY_PATH``

3. Copy ``et.dct`` (from https://github.com/Filosoft/vabamorf/tree/master/dct) to the working directory

4. Run

   ::

       printf "koer\nkass" | java -jar vabamorf-synthesize.jar S
