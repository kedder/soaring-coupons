APPCFG=./bin/python ./parts/google_appengine/appcfg.py
#APPCFG=./bin/appcfg
NODE_MODULES_BIN=node_modules/.bin

all: bin/python

.venv:
	virtualenv -p python2.7 .venv
	.venv/bin/pip install --upgrade setuptools

bin/buildout: .venv
	.venv/bin/python bootstrap.py
	touch bin/buildout


bin/python: bin/buildout buildout.cfg setup.py
	./bin/buildout
	./bin/python setup.py develop
	touch bin/python

.PHONY: run
run:
	./bin/python parts/google_appengine/dev_appserver.py --datastore_path=var/datastore.db parts/gae
#	./bin/dev_appserver parts/gae
#--use_sqlite --high_replication parts/gae

.PHONY: upload-production
upload-production: assets
	./bin/buildout -N
	$(APPCFG) update parts/gae

.PHONY: upload-testing
upload-testing: assets
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

.PHONY: npm
npm: bin/buildout
	npm install
	ln -sf `pwd`/$(NODE_MODULES_BIN)/webpack ./bin

download-prod-data:
	$(APPCFG) download_data --filename=tmp/data.csv parts/gae

watch:
	bin/webpack --progress --watch

assets: src/webpack/app.js

src/webpack/app.js: src/webpack/vendor.js
	./bin/webpack --progress

src/webpack/vendor.js: webpack-vendor.config.js package.json
	bin/webpack --progress --config webpack-vendor.config.js
