APPCFG=./bin/python ./parts/google_appengine/appcfg.py
#APPCFG=./bin/appcfg

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
	$(APPCFG) update parts/gae

.PHONY: upload-testing
upload-testing:
	./bin/buildout -N
	$(APPCFG) update parts/gae --version=test

.PHONY: test
test:
	./bin/test -c

.PHONY: coverage
coverage:
	coverage run --source=src/soaringcoupons --omit='*.html,*.txt' ./bin/test
	coverage report
	coverage html
	@echo
	@echo Now run:
	@echo
	@echo "    $$ sensible-browser htmlcov/index.html"