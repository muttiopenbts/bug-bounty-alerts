# Bug Bounty Alerts
HackerOne to Pager Duty integration for automatic alerts.

# Install
* Clone report
```
git clone <THIS REPO>
```
* Prepare python3
```
# ubuntu 20 pip installation
sudo apt update
sudo apt install python3-pip
# install pipenv
python3 -m pip install pipenv
# Make sure to add pipenv location to you path
# Optional but recommended, install https://github.com/pyenv/pyenv-installer
curl https://pyenv.run | bash
```
* Install packages
```
cd <REPO NAME>
pipenv install
```
# Configure
Two options exists for storing and accessing secrets/tokens. Either AWS Secrets manager, or environment variables.
If using AWS, populate script environment variables with following values
```
pipenv shell
export AWS_ACCESS_KEY_ID=<>
export AWS_SECRET_ACCESS_KEY=<>
export AWS_REGION_NAME=<>
export AWS_SECRET_ID=<>
```
Create key values in AWS with following names
* PD_SERVICE_ID
* PD_TOKEN
* H1_PROGRAM_NAME
* H1_API_KEY_NAME
* H1_API_KEY

If not using AWS, store secrets in follwoing environment variables
```
pipenv shell
export PD_SERVICE_ID=<>
export PD_TOKEN=<>
export H1_PROGRAM_NAME=<>
export H1_API_KEY_NAME=<>
export H1_API_KEY=<>
```
# Run
```
# pipenv shell first
python3 ./bug_bounty_alart.py
```
