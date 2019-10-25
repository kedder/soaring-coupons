VENV=ve
VEBIN=$(VENV)/bin
PYTHON=$(VEBIN)/python
PIP=$(VEBIN)/pip

all: .pip-installed

$(VENV):
	python3 -m venv $(VENV)

.pip-installed: setup.py | $(VENV)
	$(PIP) install wheel
	$(PIP) install -e .[test]
	touch .pip-installed


.PHONY: test
test: .pip-installed
	$(VEBIN)/pytest -s -v --cov src --cov-report=html --cov-report=term


.PHONY: mypy
mypy:
	$(VEBIN)/mypy src/soaringcoupons tests --strict

.PHONY: mypy-report
mypy-report:
	$(VEBIN)/mypy src/soaringcoupons tests \
		--strict \
		--html-report mypy-reports/html \
		--txt-report mypy-reports/txt
	@cat mypy-reports/txt/index.txt
	@echo "HTML report generated in mypy-reports/html/index.html"


.PHONY: black-check
black-check:
	$(VEBIN)/black --check setup.py src tests

.PHONY: black-format
black-format:
	$(VEBIN)/black setup.py src tests
