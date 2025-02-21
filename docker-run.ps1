# Runs the docker container

docker run `
    -v "${PWD}:/usr/src/qview3d/" `
    -p 127.0.0.1:8002:8002 `
    -p 127.0.0.1:8001:8001 `
    -p 127.0.0.1:8000:8000 `
    --privileged `
    -it qview3d/ubuntu:24.04