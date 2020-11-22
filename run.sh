#!/bin/sh

docker build . -t anthill_anarchy && docker run -p8081:80 anthill_anarchy 

