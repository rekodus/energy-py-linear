.PHONY: all

all: test

#  SETUP
.PHONY: setup setup-test setup-static setup-check setup-docs
setup:
	pip install --upgrade pip -q
	pip install poetry -c ./constraints.txt -q
	poetry install --with main -q

setup-test: setup
	poetry install --with test -q

setup-static: setup
	poetry install --with static -q

setup-check: setup
	poetry install --with check -q

setup-docs:
	pip install -r ./docs/requirements.txt -q

#  TEST
.PHONY: test test-ci test-validate
test: setup-test clean-test-docs test-docs
	pytest tests --showlocals --full-trace --tb=short -v -x --lf -s --color=yes --testmon --pdb

test-docs: clean-test-docs
	mkdir -p ./tests/phmdoctest
	python -m phmdoctest README.md --outfile tests/phmdoctest/test_readme.py
	python -m phmdoctest ./docs/docs/validation.md --outfile tests/phmdoctest/test_validate.py
	python -m phmdoctest ./docs/docs/how-to/dispatch-assets.md --outfile tests/phmdoctest/test_dispatch_assets.py

clean-test-docs:
	rm -rf ./tests/phmdoctest

test-ci: setup-test clean-test-docs test-docs
	coverage run -m pytest tests --tb=short --show-capture=no
	coverage report -m

#  during debug
test-validate:
	mkdir -p tests/phmdoctest
	python -m phmdoctest ./docs/docs/validation.md --outfile tests/phmdoctest/test_validate.py
	pytest tests/phmdoctest/test_validate.py --showlocals --full-trace --tb=short -v -x --lf -s --color=yes

#  CHECK
.PHONY: check
check: lint static

#  STATIC TYPING
.PHONY: static
static: setup-static
	rm -rf ./tests/phmdoctest
	mypy --config-file ./mypy.ini --pretty ./energypylinear
	mypy --config-file ./mypy.ini --pretty ./tests

#  LINTING
.PHONY: lint
lint: setup-check
	rm -rf ./tests/phmdoctest
	flake8 --extend-ignore E501 --exclude=__init__.py,poc
	ruff check .
	isort --check **/*.py --profile black
	black --check **/*.py
	poetry lock --check

#  FORMATTING
.PHONY: format
format: setup-check
	ruff check . --format
	isort **/*.py --profile black
	black **/*.py
	poetry lock --no-update

#  PUBLISH TO PYPI
-include .env.secret
.PHONY: publish
publish: setup
	poetry build
	@poetry config pypi-token.pypi $(PYPI_TOKEN)
	poetry publish

#  DOCS
.PHONY: docs docs-build
docs: setup-docs
	cd docs; mkdocs serve; cd ..

docs-build: setup-docs
	cd docs; mkdocs build; cd ..
