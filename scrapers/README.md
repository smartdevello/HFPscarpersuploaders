# scrapers

scrapers works to ...

## Execute Python script via crontab
First, check cron.d file
```bash
crontab -e
```
Next, add this link at the end of the file if python3 path is "/user/bin/python3.5" and python script path is "/home/root/start/tricare_main.py".
```bash
0 */2 * * * pgrep -n "tricare_main." || /usr/bin/python3.5 /home/root/start/tricare_main.py
```
This line means crontab makes the tricare_main.py script running every 2 hrs.