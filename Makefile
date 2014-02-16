.PHONY: tests cov htmlcov pep8 pylint docs dev-deps test-deps publish coveralls

tests:
	python test_xenon.py

cov:
	coverage erase && coverage run --include "xenon" test_xenon.py
	coverage report -m

htmlcov: cov
	coverage html

pep8:
	pep8 xenon

pylint:
	pylint --rcfile pylintrc xenon

docs:
	cd docs && make html

dev-deps:
	pip install -r dev_requirements.pip

test-deps:
	pip install -r test_requirements.pip

publish:
	python setup.py sdist bdist_wheel register upload

coveralls: test-deps cov
	coveralls
