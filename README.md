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
```
export PD_SERVICE_ID=<>
export PD_TOKEN=<>
export H1_PROGRAM_NAME=<>
export H1_API_KEY_NAME=<>
export H1_API_KEY=<>
```
# Run
```
python ./bug_bounty_alart.py
```
