# Setup guide

## Run Docker container

Ensure that docker desktop is installed.

Change directory to location of notebook file and run:

For Windows

```
docker run --rm -it -p 8888:8888 -v "%cd%":/home/jovyan/work gboeing/osmnx:latest
```

For Linux

```
docker run --rm -it -p 8888:8888 -v "$PWD":/home/jovyan/work gboeing/osmnx:latest
```

## Run bash

For Windows

```
docker run --rm -it -v "%cd%":/home/jovyan/work gboeing/osmnx:latest /bin/bash
```

For Linux

```
docker run --rm -it -v "$PWD":/home/jovyan/work gboeing/osmnx:latest /bin/bash
```

## Reference

- Github with full examples: https://github.com/gboeing/osmnx-examples
- Docker container: https://hub.docker.com/r/gboeing/osmnx
