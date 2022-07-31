
.DEFAULT_GOAL := help

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
proj_dir := $(dir $(mkfile_path))
env_file := $(proj_dir)dev-env.sh
env_template_file := $(proj_dir)dev-env.sh.template

include $(env_file)

.PHONY: help markdown dev-server

help:
	@echo markdown - Create markdown from ReStructured Text `README.rst`.
	@echo dev-server - Run the development server.

markdown:
	pandoc -s -o README.md README.rst

dev-server:
	cd $(proj_dir);
	FLASK_APP=app.py FLASK_ENV=development LOG_LEVEL=DEBUG pipenv run flask run -p 8082

$(env_file):
	cp $(env_template_file) $(env_file)

