.PHONY: run dbuild drun

run:
	SECRET_KEY=5f352 WERKZEUG_DEBUG_PIN=off FLASK_APP=webapp FLASK_ENV=development flask run --port 6123

dbuild:
	docker build -t flourish:latest .

drun:
	docker run --name flourish -p 8888:5000 --rm -e SECRET_KEY=secret flourish:latest
