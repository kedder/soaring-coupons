APPENGINE_HOME=/opt/google_appengine

.PHONY: run
run:
	$(APPENGINE_HOME)/dev_appserver.py --use_sqlite .

.PHONY: upload
upload:
	$(APPENGINE_HOME)/appcfg.py update .
