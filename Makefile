.PHONY: run dbuild drun deploy

run:
	SECRET_KEY=5f352 WERKZEUG_DEBUG_PIN=off FLASK_APP=webapp FLASK_ENV=development flask run --port 6123

dbuild:
	docker build -t nedbat/flourish:latest .

drun:
	docker run --name flourish -p 8888:5000 --rm -e SECRET_KEY=secret nedbat/flourish:latest

deploy:
	ssh drop1 "cd flourish; git pull; cd ../drop1; make run"
