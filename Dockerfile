FROM ubuntu:20.04
ENV TEST_RESULT=fail

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

# Install dependencies
RUN apt update && apt install -y \
    python3.9 \
    python3-pip

RUN python3 -m pip install pipenv

RUN curl https://pyenv.run | bash

WORKDIR '/app'

COPY ./bug_bounty_alert.py .
COPY ./Pipfile.lock .
COPY ./Pipfile .

RUN pipenv install --system --deploy

# Run the application
ENTRYPOINT python3 ./bug_bounty_alert.py