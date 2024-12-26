#!/bin/bash

# create new network
docker network create hadoop_network

# build docker image with image name hadoop-base:3.3.6
docker build -t hadoop-cluster:3.3.6-massoud-igaal -f Dockerfile-hadoop .
# running image to container, -d to run it in daemon mode
docker-compose -f docker-compose-hadoop.yml up -d
# docker-compose -f docker-compose-hadoop.yml build --no-cache && docker-compose -f docker-compose-hadoop.yml up -d

# Run Spark Cluster
if [[ "$PWD" != "spark" ]]; then
  cd spark && ./start-cluster.sh && cd ..
fi

echo "Current dir is $PWD"
