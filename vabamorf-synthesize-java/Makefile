
all: help

help:
	@echo "Commands:"
	@echo
	@echo "   javac: compile the Java files"
	@echo "     jar: make the jar file"
	@echo "    test: run a few tests"
	@echo "test_jar: test the jar-file"
	@echo "   clean: delete automatically generatable files"
	@echo

javac:
	javac -d . *.java

jar: javac
	jar cvfm vabamorf-synthesize.jar manifest.txt Synthesize.class ee

test:
	printf "palk\nkuupalk\nuba\nõu\nkoer\nkoerad\nvarumees\nNATO\nasdasdowe\naar\nkaarel\nkäärid\nteravkäärid\nvkäärid" | java Synthesize S
	printf "ilus\nkoer\nvarukoer\ntäis\nvalmis\nlauldud\njooksnud" | java Synthesize A
	printf "jooksma\notsima\njooks\njoosta" | java Synthesize V
	printf "Kaarel" | java Synthesize H

test_jar:
	printf "koer" | java -jar vabamorf-synthesize.jar S
	printf "Ansip" | java -jar vabamorf-synthesize.jar H
	printf "Rõivas" | java -jar vabamorf-synthesize.jar H

clean:
	rm -fr Synthesize.class *.jar ee
