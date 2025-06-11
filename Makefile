run:
	FLASK_APP=app.py FLASK_ENV=development flask run 

docker-build:
	docker build -t stopper-app .

docker-run:
	docker run -d --name stopper -p 8000:8000 stopper-app 