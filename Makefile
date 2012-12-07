.PHONY: run
run:
	./bin/dev_appserver --use_sqlite --high_replication parts/gae

.PHONY: upload
upload:
	./bin/buildout
	./bin/appcfg update parts/gae

.PHONY: test
test:
	./bin/test -c
