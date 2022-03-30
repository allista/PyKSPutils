.PHONY: \
	black \
	flake \
	pylint \
	mypy \
	lint \
	tests-only \
	tests

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

black:
	black $(ROOT_DIR)/KSPUtils $(ROOT_DIR)/tests

flake:
	cd "$(ROOT_DIR)/.." && flake8 --config="$(ROOT_DIR)/.flake8" "$(ROOT_DIR)"

pylint:
	cd "$(ROOT_DIR)/.." && pylint --rcfile="$(ROOT_DIR)/.pylintrc" "$(ROOT_DIR)/KSPUtils"

mypy:
	cd "$(ROOT_DIR)/.." && mypy --config-file "$(ROOT_DIR)/.mypy.ini" "$(ROOT_DIR)/KSPUtils"

lint: black flake pylint mypy

tests-only:
	pytest --cov=KSPUtils

tests: lint tests-only
