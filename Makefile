all: help

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  init                        to install python dependencies"
	@echo "  gen                         generate pages"
	@echo "  help                        to get this help"

init:
	pip3 install --upgrade -r requirements.txt

gen:
	python3 ./main.py
