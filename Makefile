all: bin/python

.venv:
	virtualenv -p python2.7 .venv

bin/buildout: .venv
	.venv/bin/python bootstrap.py
	touch bin/buildout


bin/python: bin/buildout buildout.cfg setup.py
	./bin/buildout
	./bin/python setup.py develop
	touch bin/python

.PHONY: run
run:
	./bin/python parts/google_appengine/dev_appserver.py parts/gae
#	./bin/dev_appserver parts/gae
#--use_sqlite --high_replication parts/gae

.PHONY: upload-production
upload-production:
	./bin/buildout -N
	./bin/appcfg update parts/gae

.PHONY: upload-testing
upload-testing:
	./bin/buildout -N
	./bin/appcfg update parts/gae --version=test

.PHONY: test
test:
	./bin/test -c
