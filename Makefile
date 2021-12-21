all: test mypy black

dev-environment: .pipenv-installed

.pipenv-installed: Pipfile Pipfile.lock  | $(VENV)
	pipenv install --dev
	touch .pipenv-installed

.PHONY: run
run:
	python manage.py runserver 11080

.PHONY: test
test:
	pytest -v --cov sklandymas --cov coupons --cov-report=html --cov-report=term

.PHONY: mypy
mypy:
	ENV_PATH=env.test pipenv run mypy sklandymas coupons tests

.PHONY: mypy-report
mypy-report:
	mypy sklandymas coupons tests \
		--html-report mypy-reports/html \
		--txt-report mypy-reports/txt
	@cat mypy-reports/txt/index.txt
	@echo "HTML report generated in mypy-reports/html/index.html"

.PHONY: black-check
black-check:
	black --check manage.py sklandymas coupons tests

.PHONY: black
black:
	black manage.py sklandymas coupons tests
