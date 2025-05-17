.PHONY: test
test:
	python3 -m pip install -e .
	PROJECT_DATABASE_PATH=./projects.sqlite python3 -m pytest

.PHONY: test-system
test-system:
	nohup python3 demo.py -d > demo.log 2>&1 & echo $$! > demo.pid
	PROJECT_DATABASE_PATH=./projects.sqlite python3 -m pytest -m pysteptest
	kill $$(cat demo.pid)
	rm demo.pid ./projects.sqlite

.PHONY: lint
lint:
	python3 -m ruff check .
	python3 -m ruff format . --check
	MYPYPATH=src python3 -m mypy --namespace-packages --explicit-package-bases src test

.PHONY: pin
pin:
	python3 -m pip install --only-binary :all: --upgrade pip-tools 'pip < 25.1' wheel setuptools
	python3 -m piptools compile --strip-extras --quiet --generate-hashes --upgrade requirements/prod.in -o requirements/prod.txt
	python3 -m piptools compile --strip-extras --quiet --generate-hashes --upgrade requirements/dev.in -o requirements/dev.txt

.PHONY: install
install:
	python3 -m pip install --only-binary :all: --require-hashes -r requirements/dev.txt -r requirements/prod.txt
	python3 -m pip check

.PHONY: build
build:
	python3 -m build
