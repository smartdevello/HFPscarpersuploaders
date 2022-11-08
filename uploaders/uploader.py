import os


def start():
    os.system('/usr/bin/python3.6 /home/ubuntu/Insurance-Eligibility/tricare_east_upload.py')
    os.system('/usr/bin/python3.6 /home/ubuntu/Insurance-Eligibility/tricare_west_upload.py')

start()