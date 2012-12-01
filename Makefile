.PHONY: run
run:
	./bin/dev_appserver --use_sqlite src

.PHONY: upload
upload:
	./bin/buildout
	./bin/appcfg update parts/gae

.PHONY: test
test:
	./bin/test -c
