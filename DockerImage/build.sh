#pip3 freeze > requirements.txt
docker build . -t pdf-explorer -f DockerImage/Dockerfile --network=host
docker tag pdf-explorer gcr.io/eng-flux-356316/pdf-explorer
docker push gcr.io/eng-flux-356316/pdf-explorer