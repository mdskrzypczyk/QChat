PYTHON        = python3
PIP           = pip3
SOURCEDIR     = qchat
EXAMPLES      = examples
TESTS         = test

clean: _clean_cov _clean_dist _clean_docs _clean_pyc

_clean_cov:
	@rm -rf .coverage htmlcov

_clean_dist:
	@rm -f dist/*

_clean_docs:
	@rm -rf docs/build

_clean_pyc:
	@find . -name '*.pyc' -delete

build: _clean_dist
	@$(PYTHON) setup.py sdist bdist_wheel

coverage: _clean_cov _coverage_build _coverage_report _coverage_html
	coverage run --source=$(SOURCEDIR) -m pytest $(TESTS)

_coverage_build:
	coverage run --source=$(SOURCEDIR) -m pytest $(TESTS)

_coverage_report:
	coverage report

_coverage_html:
	coverage html

install: verify build
	@$(PIP) install dist/*.whl

lint:
	@$(PYTHON) -m flake8 $(SOURCEDIR) $(TESTS)

python-deps:
	@$(PIP) install -r requirements.txt

tests:
	pytest $(TESTS)

verify: clean python-deps lint tests

.PHONY: clean lint python-deps tests verify
