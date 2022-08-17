# pip3 freeze > requirements.txt
docker build . -t pdf-check-api -f DockerImage/Dockerfile --network=host
docker tag pdf-check-api gcr.io/eng-flux-356316/pdf-check-api
docker push gcr.io/eng-flux-356316/pdf-check-api
