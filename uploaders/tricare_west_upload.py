import pandas as pd
import os
import requests
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import csv
import random
import logging
import urllib.request
from selenium.webdriver.common.keys import Keys
from PIL import Image
import json
from PyPDF2 import PdfFileMerger
from io import BytesIO


class Bot:
    def __init__(self):
        self.url4login = "https://www.tricare-west.com/idp/prov-login.fcc"
        self.url4upload = "https://www.tricare-west.com/content/hnfs/home/tw/prov/secure/app-forms/sso/upload-documents.html"
        self.url4pdf = "https://drive.google.com/file/d/1Ttg06eDSn2yVIFIVtcULlhR0e8mGHipj/view"
        self.url4list = "http://metabase-izk7e-env.us-east-1.elasticbeanstalk.com/public/question/21c6de82-1cf0-450a-8fbf-cd1a4a58d2da.json"
        self.api_key = "2c00cd3434f14892b5372c24a9581946"
        self.url4attachtomodel = "http://dmez.us-east-1.elasticbeanstalk.com/api/documents/attach_to_model.json?api_key=2c00cd3434f14892b5372c24a9581946"
        self.headers = {'Cookie': 'CAKEPHP=91f37b149b22c2518b0b6c304ed49502'}
        self.abs_path = os.path.abspath(os.path.dirname(__file__))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        try:
            if self.drive is not None:
                self.drive.quit()
        except Exception as e:
            pass

    def browser_init(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--ignore-certificate-errors')
        drive = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
        drive.get(self.url4login)
        drive.set_window_size(1440, 1440)
        time.sleep(3)
        user_name = drive.find_element_by_id('username_bene')
        user_name.send_keys('homefrontpumpsw1')
        password = drive.find_element_by_id('password_bene')
        password.send_keys('Hudspeth815!@#')
        time.sleep(2)
        login_button = drive.find_element_by_id('prov-login').click()
        time.sleep(4)
        self.drive = drive
    
    def main(self):
        tricare_list = requests.get(self.url4list).json()
        print(len(tricare_list))
        url_list = []
        for tricare in tricare_list:
            
            if tricare['id'] == 2:
                print(tricare)
                url_list.append(tricare['url'])

        for patient_info in url_list:
            response = self.send_document_claims(patient_info)
            if response is False:
                logging.warning('failed')

    def is_system_ok(self, drive):
        try:
            err_msg = drive.find_element_by_xpath("//div[@id='rightContainerComponent1']/div").text
            logging.warning("System is experiencing technical difficulties.")
            return False
        except Exception as e:
            logging.warning("The system is okay!")
            return True
        
    def is_validate_patient(self, drive):
        if "Change Patient" in drive.find_element_by_id("TricareButton_0").text:
            logging.warning('This patient info is valid.')
            return True
        else:
            logging.warning('This patient info is invalid. Pay attention to use the valid info.')
            return False

    def download_file(self, download_url, filename):
        # NOTE: If the pdf file is located in the Google Drive
        file_id = download_url.split('/')[-2]
        file_path = "https://drive.google.com/uc?export=download&id={}".format(file_id)
        response = urllib.request.urlopen(file_path)
        # NOTE: If the pdf file is located in the AWS S3
        #response = urllib.request.urlopen(download_url)

        file = open(filename + ".pdf", 'wb')
        file.write(response.read())
        file.close()

    def get_dob(self, customer_dob):
        dob = ""
        print(customer_dob)
        tmp = customer_dob.split(' ')[0].split('-')
        dob = tmp[1] + '/' + tmp[2] + '/' + tmp[0]
        return dob

    def send_document_claims(self, info_url):
        print(info_url)
        try:
            info_text = requests.get(info_url + '?api_key=' + self.api_key).text
            info_json = json.loads(info_text)
        except Exception as e:
            print(e)
            return False
        
        model_id = info_json['cmn']['id']
        dob = self.get_dob(info_json['cmn']['customers_payer']['customer']['customer_dob'])
        dbn = info_json['cmn']['customers_payer']['member_number']
        info = {
            'dbn': dbn,
            'dob': dob,
        }
        print(info)

        signed_cmn_links = []
        for doc in info_json['cmn']['documents']:
            if doc['type'] == 'Signed CMN':
                signed_cmn_links.append({'id': doc['id'], 'url': doc['s3_url']})
        if len(signed_cmn_links) == 0:
            logging.warning('The Signed CMN Not Exist!')
            self.update_cmn_status_failed(str(model_id))
            return False

        signed_cmn_paths = []
        for signed_cmn_link in signed_cmn_links:
            print(signed_cmn_links)
            try:
                r = requests.get(signed_cmn_link['url'])
                fo = open(self.abs_path + "/" + 'west_tmp{}.pdf'.format(signed_cmn_link['id']), 'wb')
                fo.write(r.content)
                signed_cmn_paths.append(self.abs_path + "/" + 'west_tmp{}.pdf'.format(signed_cmn_link['id']))
                fo.close()
            except Exception as e:
                logging.warning("The s3 url doesn't exist")
                self.update_cmn_status_failed(str(model_id))
                print(e)
                return False
        try:
            os.remove(self.abs_path + "/" + 'west_cmn.pdf')
        except Exception as e:
            pass
        merger = PdfFileMerger()
        for pdf in signed_cmn_paths:
            merger.append(pdf)

        with open(self.abs_path + "/" + 'west_cmn.pdf', "wb") as fout:
            merger.write(fout)

        for signed_cmn_path in signed_cmn_paths:
            try:
                os.remove(signed_cmn_path)
            except Exception as e:
                pass
        NPI = '1932759131'
        drive = self.drive
        drive.get(self.url4upload)
        iwait = random.randint(15, 20) + random.random()
        print(iwait)
        time.sleep(iwait)
        print(drive.current_url)
        drive.find_element_by_id("tins").click()
        iwait = random.randint(0, 1) + random.random()
        time.sleep(iwait)
        drive.find_elements_by_xpath("//select[@id='tins']/option")[1].click()
        iwait = random.randint(0, 1) + random.random()
        time.sleep(iwait)
        drive.find_element_by_id("npi").send_keys(NPI)
        iwait = random.randint(0, 1) + random.random()
        time.sleep(iwait)
        drive.find_element_by_id("prov-sso-submit").click()
        iwait = random.randint(10, 13) + random.random()
        time.sleep(iwait)

        drive.switch_to_window(drive.window_handles[1])
        iwait = random.randint(25, 28) + random.random()
        time.sleep(iwait)

        while True:
            if self.is_system_ok(drive):
                break
            else:
                iwait = random.randint(300, 400) + random.random()
                time.sleep(iwait)
                continue

        drive.find_elements_by_id("ProviderAttachmentsSendDocumentView_0-category")[0].click()
        iwait = random.randint(1, 2) + random.random()
        time.sleep(iwait)
        drive.find_elements_by_xpath("//ul[@id='ux_dropdown_Menu_0']/li")[1].click()
        iwait = random.randint(1, 2) + random.random()
        time.sleep(iwait)

        drive.find_elements_by_id("ProviderAttachmentsSendDocumentView_0-category")[1].click()
        iwait = random.randint(1, 2) + random.random()
        time.sleep(iwait)
        drive.find_elements_by_xpath("//ul[@id='ux_dropdown_Menu_1']/li")[3].click()
        iwait = random.randint(1, 2) + random.random()
        time.sleep(iwait)

        checkbox = drive.find_element_by_xpath("//input[@id='Radio_1_input']")
        drive.execute_script("arguments[0].click();", checkbox)
        iwait = random.randint(1, 2) + random.random()
        time.sleep(iwait)

        drive.find_element_by_id("ux_input__NativeInput_1").send_keys(info["dbn"])
        iwait = random.randint(2, 3) + random.random()
        time.sleep(iwait)
        
        drive.find_element_by_xpath("//span[@id='ux_input__MaskedInput_0']/input[@type='text']").send_keys(info["dob"])
        iwait = random.randint(1, 2) + random.random()
        time.sleep(iwait)

        drive.find_element_by_id("SecuredFormButton_0").click() # clicking 'validate patient' button. If invalid, return False
        iwait = random.randint(10, 15) + random.random()
        time.sleep(iwait)
        if self.is_validate_patient(drive) is not True:
            # return False
            print('validate patient failed')
        
        drive.save_screenshot(self.abs_path + "/" + 'screenshot0.png')
        iwait = random.randint(2, 3) + random.random()
        time.sleep(iwait)
        
        drive.find_element_by_id("Textarea_0").send_keys("Please see attached Certificate of Medical Necessity")
        iwait = random.randint(2, 3) + random.random()
        time.sleep(iwait)

        drive.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        iwait = random.randint(1, 2) + random.random()
        time.sleep(iwait)

        iwait = random.randint(3, 5) + random.random()
        time.sleep(iwait)
        abspath = os.path.abspath(os.path.dirname(__file__))
        file_path = abspath + "/west_cmn.pdf"
        print(file_path)
        drive.find_element_by_xpath("//*[@type='file']").send_keys(file_path)
        iwait = random.randint(5, 8) + random.random()
        time.sleep(iwait)

        drive.save_screenshot(self.abs_path + "/" + 'screenshot1.png')
        iwait = random.randint(2, 3) + random.random()
        time.sleep(iwait)
        
        drive.find_element_by_id("SecuredFormButton_1").click()
        iwait = random.randint(8, 12) + random.random()
        time.sleep(iwait)
        drive.save_screenshot(self.abs_path + "/" + 'screenshot2.png')
        iwait = random.randint(3, 5) + random.random()
        time.sleep(iwait)

        try:
            image0 = Image.open(self.abs_path + "/" + "screenshot0.png")
            im0 = image0.convert('RGB')
            image1 = Image.open(self.abs_path + "/" + "screenshot1.png")
            im1 = image1.convert('RGB')
            image2 = Image.open(self.abs_path + "/" + "screenshot2.png")
            im2 = image2.convert('RGB')
        except Exception as e:
            logging.warning('screenshot error')

        pdf_path = self.abs_path + "/" + str(dbn) + '-' + str(dob.replace('/', '')) + '-' + time.strftime('%Y%m%d') + '.pdf'
        print(pdf_path)
        try:
            im0.save(pdf_path, save_all=True, append_images=[im1, im2])

            payload1={'model': 'Cmns', 'model_id': str(model_id), 'type': 'Submission Confirmation'}
            files1=[('file', open(pdf_path,'rb'))]
            response = requests.request("POST", self.url4attachtomodel, headers=self.headers, data=payload1, files=files1)
            print(response.text)
            self.update_cmn_status_success(str(model_id))
        except Exception as e:
            logging.warning('pdf creating error')
            self.update_cmn_status_failed(str(model_id))

        drive.close()
        drive.switch_to_window(drive.window_handles[0])

        # payload2={'model': 'Cmns', 'model_id': str(model_id),}
        # files2=[('file', open(self.abs_path + "/cmn.pdf",'rb'))]
        # response = requests.request("POST", self.url4attachtomodel, headers=self.headers, data=payload2, files=files2)
        # print(response.text)

        try:
            os.remove(self.abs_path + "/" + 'screenshot0.png')
        except Exception as e:
            pass
        try:
            os.remove(self.abs_path + "/" + 'screenshot1.png')
        except Exception as e:
            pass
        try:
            os.remove(self.abs_path + "/" + 'screenshot2.png')
        except Exception as e:
            pass
        try:
            os.remove(self.abs_path + "/" + 'west_cmn.pdf')
        except Exception as e:
            pass
        try:
            os.remove(pdf_path)
        except Exception as e:
            pass
        return True
    
    def update_cmn_status_success(self, model_id):
        post_url = "http://dmez.us-east-1.elasticbeanstalk.com/api/cmns/edit/" + model_id + ".json?api_key=" + self.api_key
        payload={'id': model_id, 'status_id': '74'}
        files=[]
        response = requests.request("POST", post_url, headers=self.headers, data=payload, files=files)
    
    def update_cmn_status_failed(self, model_id):
        post_url = "http://dmez.us-east-1.elasticbeanstalk.com/api/cmns/edit/" + model_id + ".json?api_key=" + self.api_key
        payload={'id': model_id, 'status_id': '73'}
        files=[]
        response = requests.request("POST", post_url, headers=self.headers, data=payload, files=files)

with Bot() as scraper:
    scraper.browser_init()
    scraper.main()