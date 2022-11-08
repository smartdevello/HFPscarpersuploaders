import pandas as pd
import os
import requests
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import time
import csv
import random
import logging
import urllib.request
from selenium.webdriver.common.keys import Keys
from PIL import Image
import json
import random
from io import BytesIO
from webdriver_manager.firefox import GeckoDriverManager


class Bot:
    def __init__(self):
        self.url = "https://www.dhl.com/global-en/home/tracking.html"
        self.abs_path = os.path.abspath(os.path.dirname(__file__))
        self.url4metabase = "http://metabase-izk7e-env.us-east-1.elasticbeanstalk.com/public/question/9db23b9b-c165-400c-b6b0-b14ba8f9c794.json"
        self.url4attachtomodel = "http://dmez.us-east-1.elasticbeanstalk.com/api/documents/attach_to_model.json?api_key=2c00cd3434f14892b5372c24a9581946"
        self.headers = {'Cookie': 'CAKEPHP=91f37b149b22c2518b0b6c304ed49502'}
        self.pdfname = 'dhl_confirm.pdf'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        try:
            if self.drive is not None:
                self.drive.quit()
        except Exception as e:
            pass

    def browser_init(self):
        options = FirefoxOptions()
        options.add_argument("--headless")
        binary = FirefoxBinary('/usr/bin/firefox-esr')
        drive = webdriver.Firefox(firefox_binary=binary, executable_path=GeckoDriverManager().install(), options=options)
        drive.get(self.url)
        iwait = random.randint(10, 15) + random.random()
        time.sleep(iwait)
        try:
            drive.find_element_by_id("accept-recommended-btn-handler").click()
            iwait = random.randint(5, 8) + random.random()
            time.sleep(iwait)
        except Exception as e:
            pass
        self.drive = drive
    

    def get_metabase(self):
        mb_qry = requests.get(self.url4metabase).json()
        return mb_qry


    def confirm_delivery(self, tracking_number, model_id):
        drive = self.drive
        try:
            tracking_number_input = drive.find_elements_by_xpath("//input[@name='tracking-id']")[1]
            print(tracking_number)
            tracking_number_input.clear()
            tracking_number_input.send_keys(tracking_number)
            iwait = random.randint(2, 3) + random.random()
            time.sleep(iwait)
            drive.find_element_by_xpath("//button[contains(@class, 'js--tracking--input-submit')]").click()
            iwait = random.randint(3, 5) + random.random()
            time.sleep(iwait)
            
            detail_btns = drive.find_elements_by_xpath("//a[@href='javascript:void(0);']")
            for btn in detail_btns:
                btn.click()
                iwait = random.randint(2, 3) + random.random()
                time.sleep(iwait)
            drive.execute_script("window.scrollTo(0, 0)")
            iwait = random.randint(2, 3) + random.random()
            time.sleep(iwait)

            drive.set_window_size(1440, 5000)
            iwait = random.randint(2, 3) + random.random()
            time.sleep(iwait)
            img = Image.open(BytesIO(drive.find_element_by_tag_name('body').screenshot_as_png))
            im1 = img.convert('RGB')
            im1.save(self.abs_path + '/' + self.pdfname, "PDF", quality=100)

            iwait = random.randint(3, 5) + random.random()
            time.sleep(iwait)
            #TODO post pdf file
            self.post_pdf(model_id)
            try:
                os.remove(self.abs_path + '/' + self.pdfname)
            except Exception as e:
                pass
            return True
        except Exception as e:
            return False


    def post_pdf(self, model_id):
        payload={'model': 'Shipments', 'model_id': model_id, 'type': 'Tracking Screenshot'}
        files=[('file', open(self.abs_path + '/' + self.pdfname,'rb'))]
        response = requests.request("POST", self.url4attachtomodel, headers=self.headers, data=payload, files=files)
        print(response.text)


    def main(self):
        mb_qry = self.get_metabase()
        logging.warning('------{}----'.format(len(mb_qry)))
        if len(mb_qry) is 0:
            logging.warning('metabase is empty.')
            return
        
        for obj in mb_qry:
            if obj['carrier_id'] == 3:
                rst = self.confirm_delivery(obj["tracking"], obj["model_id"])
                if rst:
                    logging.warning("Success in DHL Delivery Confirmation")
                else:
                    logging.warning("Failed in DHL Delivery Confirmation")

with Bot() as scraper:
    scraper.browser_init()
    scraper.main()