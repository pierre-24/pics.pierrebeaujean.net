all: help
.PHONY: tests

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  init                        to install python dependencies"
	@echo "  gen                         generate pages"
	@echo "  help                        to get this help"
	@echo "  lint                        to lint backend code (flake8)"

init:
	pip3 install --upgrade -r requirements.txt

gen:
	python3 ./main.py

lint:
	flake8 mosgal tests --max-line-length=120 --ignore=N802

tests:
	python -m unittest discover -s tests
