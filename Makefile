.PHONY: \
	black \
	lint \
	tests-only \
	tests

black:
	black KSPUtils tests

lint: black
	flake8
	pylint KSPUtils
	mypy KSPUtils

tests-only:
	pytest --cov=KSPUtils

tests: lint tests-only
