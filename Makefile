# Makefile for eleve

.PHONY: help test testlib testcov testdoc clean doc testall testdoc

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  help           prints this help"
	@echo "  doc            build doc after tests run"
	@echo "  doc-notest     build doc without running all test (just documentations ones)"
	@echo "  test           runs unit tests"
	@echo "  testlib        runs doctests on lib only"
	@echo "  testlib        runs doctests on documentation only"
	@echo "  testall        runs all tests (unit+doc+rst) and generate html report for coverage"
	@echo "  testcov        runs all tests and give copact coverage report"
	@echo "  publish        publish it to pipy"
	@echo "  publish-doc    publish the doc to pythonhosted.org"

clean-doc:
	rm -rf docs/_build/ docs/_templates/

doc: testdoc
	make -C ./docs html

doc-notest:
	make -C ./docs html

test:
	py.test -v ./tests --cov eleve --cov-report html

testlib: 
	py.test -v ./eleve --doctest-module

testdoc:
	py.test -v ./README.rst ./docs --doctest-glob='*.rst'

testall: 
	py.test -v ./tests ./eleve ./README.rst ./docs --doctest-module --doctest-glob='*.rst' --cov eleve --cov-report html

testcov:
	py.test -v ./tests ./eleve ./README.rst ./docs --doctest-module --doctest-glob='*.rst' --cov eleve --cov-report term-missing

clean:
	# removing .pyc filesin
	-rm -r build
	-find ./ -iname *.pyc | xargs rm
	-find ./ -iname *.py~ | xargs rm
	-find ./eleve -iname *.so | xargs rm

all: help

build_cython::
	cd eleve; python setup.py build_ext --inplace

publish:
	python setup.py sdist upload

publish-doc: doc
	python setup.py upload_docs --upload-dir docs/_build/html/
