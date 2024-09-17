FROM python:3.12.1-bullseye

ARG INSTALL_DIR=${INSTALL_DIR}

RUN mkdir -p $INSTALL_DIR
WORKDIR $INSTALL_DIR

COPY ./pyproject.toml ./poetry.lock ./
RUN pip3 install poetry && poetry config virtualenvs.create false
COPY wait-for /bin/wait-for
RUN poetry install

ARG USERNAME=$USERNAME
RUN useradd -m $USERNAME
USER $USERNAME




