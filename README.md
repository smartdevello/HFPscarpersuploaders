# HFPSCRAPERSUPLOADERS

HFPSCRAPERSUPLOADERS works to
- scape patients'info from tricare east and tricare west.
- upload some documents
## AWS EC2 instance access information
hostname: 18.216.144.113

username: ubuntu

pem file: /pem/key.pem

## Environment Required

First update and upgrade your system(Ubuntu 18.04 or 20.04) to ensure that your shipped version of Python 3 is up-to-date.

```bash
sudo apt update
sudo apt -y upgrade
```
Then, check version of Python
```bash
python3 -V
```
Next, install pip
```bash
sudo apt install -y python3-pip
```
After that, install Google Chrome & Firefox
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```
```bash
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A6DCF7707EBC211F
sudo apt-add-repository "deb http://ppa.launchpad.net/ubuntu-mozilla-security/ppa/ubuntu focal main"
sudo apt update
```
Finally, install packages using requirements.txt
```bash
pip3 install -r requirements.txt
```
## How can add a new script?
Let's say there's main.py at /home/ubuntu/HFPscarpersuploaders/demo/main.py

Then, you can execute it using crontab.

First, check cron.d file
```bash
crontab -e
```
Next, add this line at the end of the file.
```bash
*/3 * * * * pgrep -n "main.py" || /usr/bin/python3.6 /home/ubuntu/HFPscarpersuploaders/demo/main.py
```
This line means crontab makes the main.py script running every 3 minutes.

[reference video](https://drive.google.com/file/d/1OZSm4cKLDkoUIxnyrV47MVo0EZt5sHOG/view?usp=sharing)

## In general, how to execute Python script via crontab
First, check cron.d file
```bash
crontab -e
```
Next, add this line at the end of the file if python3 path is "/user/bin/python3.5" and python script path is "/home/root/start/mainuploader.py".
```bash
0 */2 * * * pgrep -n "mainuploader." || /usr/bin/python3.5 /home/root/start/mainuploader.py
```
This line means crontab makes the mainuploader.py script running every 2 hrs.
