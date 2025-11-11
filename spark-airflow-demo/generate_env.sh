#!/bin/bash

cat <<EOF > .env
AIRFLOW_UID=$(id -u)
AIRFLOW_GID=0
AIRFLOW__CORE__FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
EOF