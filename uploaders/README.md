# uploaders

uploaders works to ...

## Execute Python script via crontab
First, check cron.d file
```bash
crontab -e
```
Next, add this link for uploader.py at the end of the file if python3 path is "/user/bin/python3.5" and python script path is "/home/root/start/uploader.py".
```bash
0 */2 * * * pgrep -n "uploader." || /usr/bin/python3.5 /home/root/start/uploader.py
```
Then, add two lines for dhl.py and fedex.py
```bash
0 */2 * * * pgrep -n "dhl." || /usr/bin/python3.5 /home/root/start/dhl.py
0 */2 * * * pgrep -n "fedex." || /usr/bin/python3.5 /home/root/start/fedex.py
```
This line means crontab makes the script running every 2 hrs.