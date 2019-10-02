.PHONY: tests cov htmlcov pep8 pylint docs dev-deps test-deps publish \
	coveralls clean

tests:
	python test_xenon.py

cov:
	coverage erase && coverage run --include "xenon/*.py" \
		--omit "xenon/__init__.py" test_xenon.py
	coverage report -m

htmlcov: cov
	coverage html

pep8:
	pep8 xenon

pylint:
	pylint --rcfile pylintrc xenon

docs:
	cd docs && make html

test-deps:
	pip install -r test_requirements.pip

publish:
	rm -rf dist/*
	python setup.py sdist bdist_wheel
	twine upload dist/*
	python setup.py develop

coveralls: test-deps cov
	coveralls

clean:
	python setup.py clean --all
	find . -not -path '*/.git/*' -name '*.py[co]' -exec rm -f '{}' ';'
	find . -name '*.err' -exec rm -f '{}' ';'
	rm -rf __pycache__ dist build htmlcov
	rm -f .coverage
