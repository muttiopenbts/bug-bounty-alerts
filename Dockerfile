FROM ubuntu:20.04

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
# Timezone needed in aws ecs
ENV TZ=America/Los_Angeles

# Install dependencies
RUN apt update && apt install -y \
    python3.9 \
    git \
    python3-pip

RUN python3 -m pip install pipenv

RUN curl https://pyenv.run | bash

RUN git clone https://github.com/muttiopenbts/bug-bounty-alerts.git

WORKDIR './bug-bounty-alerts'

RUN pipenv install --system --deploy

# Run the application
ENTRYPOINT python3 ./bug_bounty_alert.py
# ENTRYPOINT python3 -c "exec(\"import sys\nwhile 1:\n\tprint(f'...')\")"