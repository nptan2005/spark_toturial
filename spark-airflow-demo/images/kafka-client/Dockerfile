FROM python:3.11-slim

# -------------------------------------------------
# System libs
# -------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget curl unzip build-essential \
    libaio-dev \
    zsh git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Python requirements
# -------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# -------------------------------------------------
# Oracle Instant Client (ARM64)
# -------------------------------------------------
COPY instantclient/*.zip /tmp/ic.zip

RUN unzip /tmp/ic.zip -d /opt/oracle && rm /tmp/ic.zip

ENV ORACLE_HOME="/opt/oracle/instantclient_23_6"
ARG LD_LIBRARY_PATH=""
ENV LD_LIBRARY_PATH="${ORACLE_HOME}:${LD_LIBRARY_PATH:-}"

# -------------------------------------------------
# ZSH + Starship
# -------------------------------------------------
RUN curl -fsSL https://starship.rs/install.sh -o /tmp/starship.sh && \
    sh /tmp/starship.sh -y && \
    rm /tmp/starship.sh

COPY configs/zshrc /etc/zsh/zshrc
COPY configs/starship.toml /etc/starship.toml

# -------------------------------------------------
# App
# -------------------------------------------------
COPY app/ /app
WORKDIR /app

CMD ["python", "producer.py"]