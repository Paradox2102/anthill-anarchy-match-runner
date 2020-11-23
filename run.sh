#!/bin/sh

SERVICE_PORT=8081
IMAGE_NAME=anthill_anarchy

docker build . -t ${IMAGE_NAME} && docker run -p${SERVICE_PORT}:80 ${IMAGE_NAME}