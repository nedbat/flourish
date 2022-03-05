.PHONY: sass livesass run dbuild drun deploy help

.DEFAULT_GOAL := help

SCSS = templates/style.scss
SASSARGS = --style=compact --sourcemap=none $(SCSS)

sass:	## Build the CSS
	sass $(SASSARGS) templates/style.css

livesass: ## For live-editing the CSS
	sass --watch $(SASSARGS)

run:	## Run locally
	SECRET_KEY=5f352 WERKZEUG_DEBUG_PIN=off FLASK_APP=webapp FLASK_ENV=development flask run --port 6123

dbuild:	## Build the docker image
	docker build -t nedbat/flourish:latest .

drun:	## Run the docker image locally
	docker run --name flourish -p 8888:5000 --rm -e SECRET_KEY=secret nedbat/flourish:latest

deploy:	## Deploy to drop1
	ssh drop1 "cd ~/flourish; git pull; cd ~/drop1; docker-compose up --build -d flourish"

help:	## Show this help.
	@# Adapted from https://www.thapaliya.com/en/writings/well-documented-makefiles/
	@echo Available targets:
	@awk -F ':.*##' '/^[^: ]+:.*##/{printf "  \033[1m%-20s\033[m %s\n",$$1,$$2} /^##@/{printf "\n%s\n",substr($$0,5)}' $(MAKEFILE_LIST)
