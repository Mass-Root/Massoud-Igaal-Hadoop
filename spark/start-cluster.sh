#!/bin/bash

# docker build --no-cache -t spark-massoud-igaal:3.5.4 .
docker build -t spark-massoud-igaal:3.5.4 .
docker-compose up -d
