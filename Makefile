.PHONY: run
run:
	./bin/dev_appserver --use_sqlite --high_replication parts/gae

.PHONY: upload-production
upload-production:
	./bin/buildout
	./bin/appcfg update parts/gae

.PHONY: upload-testing
upload-testing:
	./bin/buildout
	./bin/appcfg update parts/gae --version=test

.PHONY: test
test:
	./bin/test -c
