FROM python:3.9-slim

ARG IP
ARG PORT

# download and install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY . .

RUN chmod +x ./install.sh

RUN ./install.sh

RUN chmod +x ./run_prod.sh

WORKDIR /server

RUN echo echo "Port: $PORT"

EXPOSE $PORT

WORKDIR /

CMD ["sh", "./run_prod.sh"]