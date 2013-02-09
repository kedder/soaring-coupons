.PHONY: run
run:
	./bin/dev_appserver --use_sqlite --high_replication parts/gae

.PHONY: upload
upload-production:
	./bin/buildout
	./bin/appcfg update parts/gae

upload-testing:
	./bin/buildout
	./bin/appcfg update parts/gae --version=test

.PHONY: test
test:
	./bin/test -c
