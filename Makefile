
.DEFAULT_GOAL := help

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
proj_dir := $(dir $(mkfile_path))
env_file := $(proj_dir)dev-env.sh
env_template_file := $(proj_dir)dev-env.sh.template
bundle_js := $(proj_dir)static/bundle.js
main_js := $(proj_dir)src/js/main.js
node_modules := $(proj_dir)node_modules

include $(env_file)

.PHONY: help markdown dev-server distribution

help:
	@echo markdown - Create markdown from ReStructured Text `README.rst`.
	@echo dev-server - Run the development server.

markdown:
	pandoc -s -o README.md README.rst

dev-server:
	cd $(proj_dir);
	FLASK_APP=app.py FLASK_ENV=development LOG_LEVEL=DEBUG pipenv run flask run -p 8082

distribution: $(bundle_js)

$(env_file):
	cp $(env_template_file) $(env_file)

$(bundle_js): $(main_js) $(node_modules)
	npm run dev-build

$(node_modules):
	cd $(proj_dir)
	npm install

