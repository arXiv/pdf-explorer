#pip3 freeze > requirements.txt
docker build . -t pdf-explorer -f DockerImage/Dockerfile --network=host
docker run -p 5000:5000 pdf-explorer