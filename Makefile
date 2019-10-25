VENV=ve
VEBIN=$(VENV)/bin
PYTHON=$(VEBIN)/python
PIP=$(VEBIN)/pip

all: .pip-installed

$(VENV):
	python3 -m venv $(VENV)

.pip-installed: requirements.txt requirements-dev.txt | $(VENV)
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	touch .pip-installed


.PHONY: run
run: .pip-installed
	$(PYTHON) manage.py runserver 10080


.PHONY: test
test: .pip-installed
	$(VEBIN)/pytest -s -v --cov sklandymas --cov-report=html --cov-report=term


.PHONY: mypy
mypy:
	$(VEBIN)/mypy sklandymas tests

.PHONY: mypy-report
mypy-report:
	$(VEBIN)/mypy sklandymas tests \
		--strict \
		--html-report mypy-reports/html \
		--txt-report mypy-reports/txt
	@cat mypy-reports/txt/index.txt
	@echo "HTML report generated in mypy-reports/html/index.html"


.PHONY: black-check
black-check:
	$(VEBIN)/black --check manage.py sklandymas coupons tests

.PHONY: black-format
black-format:
	$(VEBIN)/black manage.py sklandymas coupons tests
