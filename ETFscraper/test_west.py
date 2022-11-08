import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from webdriver_manager.chrome import ChromeDriverManager
import fitz
import re
from datetime import date
import json
import requests
import locale
locale.setlocale( locale.LC_ALL, 'en_US.UTF-8' ) 

class Bot:
    def __init__(self):
        self.url4login = "https://www.tricare-west.com/idp/prov-login.fcc"
        self.username = "homefrontpumpsw1"
        self.password = "815!@#Hudspeth"
        self.report_url = "https://www.tricare-west.com/content/hnfs/home/tw/prov/secure/app-forms/sso/view-remits.html"
        self.NPI = "1932759131"
        self.abs_path = os.path.abspath(os.path.dirname(__file__))
        self.doccount = 0
        self.records = []
        self.posturl = "http://dmez.us-east-1.elasticbeanstalk.com/api/payments/frompayer.json?api_key=2c00cd3434f14892b5372c24a9581946"
        self.post_payer_id = 2

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
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--ignore-certificate-errors')

        chrome_options.add_experimental_option('prefs',  {
            "download.default_directory": self.abs_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
            }
        )
        drive = webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=chrome_options)


        drive.get(self.url4login)
        drive.set_window_size(1440, 1440)
        time.sleep(3)
        drive.find_element_by_id('username_bene').send_keys(self.username)
        drive.find_element_by_id('password_bene').send_keys(self.password)
        time.sleep(2)
        drive.find_element_by_id('prov-login').click()
        time.sleep(4)
        self.drive = drive

    def main(self):
        self.doccount = 1
        if os.path.exists(os.path.join(self.abs_path, str(self.doccount) + "west.pdf")):
            time.sleep(0.5)
            self.process_pdf()
            with open(os.path.join(self.abs_path,  str(self.doccount) + "west.json"), "w") as outfile:
                for record in self.records:
                    record["Deductible"] = locale.atof(self.deductible) if self.deductible else ""
                json.dump(self.records, outfile)
                self.records = []            
            self.post_info_to_dmez( str(self.doccount) + "west.pdf",  str(self.doccount) + "west.json")
    def post_info_to_dmez(self, pdf_path, json_path):

        payload={'payer_id': self.post_payer_id}
        pdf_file = open(os.path.join(self.abs_path, pdf_path), 'rb')
        json_file = open(os.path.join(self.abs_path, json_path), 'rb')
        files=[
            ('pdf', (pdf_path, pdf_file, 'application/pdf')),
            ('json', (json_path, json_file, 'application/json'))
        ]
        headers = {
            'Cookie': 'CAKEPHP=730eb20cd69b0b638fbad88c088ee15b'
        }

        response = requests.request("POST", self.posturl, headers=headers, data=payload, files=files)

        print(response.text)

    def get_check_number(self, doc):
        self.check_number = ""
        for p in doc.pages():
            page_content = p.getText()
            m = re.match(r'.*\n([0-9A-Z\s]+)\nDUPLICATE\nCOPY\n', page_content, re.DOTALL)
            if m is not None:
                self.check_number = m.group(1)
                return

    def get_message_codes(self, doc):
        for p in doc.pages():
            page_content = p.getText("text", clip=fitz.Rect(144, 0, 504, 792))
            m = re.match(r'.*(REASON\sCODES:\n.+)(MESSAGE\sCODES:\n.+)', page_content, re.DOTALL)
            if m is not None:
                self.reason_codes = m.group(1)[14:]
                self.message_codes = m.group(2)[15:]
                self.reason_codes = self.process_reasoncodes(self.reason_codes)
                self.message_codes = self.process_messagecodes(self.message_codes)
                return
            else:
                m = re.match(r'.*(MESSAGE\sCODES:\n.+)', page_content, re.DOTALL)
                if m is not None:
                    self.reason_codes = ""
                    self.message_codes = m.group(1)[15:]
                    self.reason_codes = self.process_reasoncodes(self.reason_codes)
                    self.message_codes = self.process_messagecodes(self.message_codes)
                    return
                    
    def process_pdf(self):
        
        doc = fitz.open(os.path.join(self.abs_path, str(self.doccount) + "west.pdf"))
        self.info = doc[0].getText("text", clip=fitz.Rect(360,144,576,252))
        self.info = re.match(r'([A-Z]+\s[0-9].{2}\s[0-9]+\n)([0-9]*\n)?([0-9]*\n)?([0-9\.\,]*\n)?Date\sof\sRemittance', self.info, re.DOTALL)

        self.get_check_number(doc)
        self.get_message_codes(doc)

        self.process_pages(doc)
        # for p in doc.pages():
        #     self.process_page(p)
        doc.close()        
        # os.remove(os.path.join(self.abs_path, str(self.doccount) + ".pdf"))
        

    def get_date(self, date):
        m = re.match(r'([0-9]{2})([0-9]{2})([0-9]{2})', date)
        return m.group(1) + "/" + m.group(2) + "/" + m.group(3)

    def process_row(self, patient, claim_number, data, section_adjustment):
        m = re.match(r'([0-9]+)\s([0-9]+)\n([A-Z0-9]+)\s([A-Z0-9]+)\n([0-9]+)\n([0-9\.\,]+)\n([0-9\.\,]+)\n([0-9A-Z]+)?\n?([0-9][0-9\.\,]+)\n([0-9\.\,]+)\n([0-9\.\,]+)\n([0-9\.\,]+)\n(.*)', data, re.DOTALL)
        
        message_code = m.group(9)
        for x in re.findall(r'[0-9]+\n[0-9\.\,]+\n[0-9\.\,]+\n([0-9\.\,]+)\n[0-9\.\,]+\n[0-9\.\,]+\n[0-9\.\,]+\n', m.group(13)):
            message_code+=x
        section = {
            "Check Number": self.check_number,
            "Claim Number": claim_number,
            "Check Amount": locale.atof(self.info.group(4).strip()),
            "Date of Remittance": self.info.group(1).strip(),
            "Patient Account Number": patient[0],
            "Patient Name": patient[1],
            "Dates of Service Begin": self.get_date(m.group(1)),
            "Dates of Service End": self.get_date(m.group(2)),
            "Procedure": m.group(3),
            "Modifier": m.group(4),
            "# of Srvcs": locale.atof(m.group(5)),
            "Total Charges": locale.atof(m.group(6)),
            "Allowed Covered Charges": locale.atof(m.group(7)),
            "Reason Code": m.group(8).strip() if m.group(8) else "",
            "Message Code": message_code,
            "Cost Share": locale.atof(m.group(10)),
            "Copay": locale.atof(m.group(11)),
            "TRICARE Payment": locale.atof(m.group(12)),
            "Reason Codes": self.reason_codes,
            "Message Codes": self.message_codes,
            "Section Adjustment": section_adjustment, 
            "Section Adjustment Reason": ""
        }

        if section_adjustment is not 0:
            section["Section Adjustment Reason"] = "Less Previous Payment"
        self.records.append(section)

    def process_reasoncodes(self, data):        
        res = {}
        subcodes = re.split(r'([A-Z]\d.{3,3}\n)', data, re.DOTALL)
        for i in range(1, len(subcodes) -1, 2):
            res[subcodes[i].strip()] = subcodes[i+1].strip().replace("\n", " ")
            # res.append({subcodes[i].strip(): subcodes[i+1].strip().replace("\n", " ")})
        return res
    def process_messagecodes(self, data):
        res = {}
        subcodes = re.split(r'(\d\n)', data, re.DOTALL)
        for i in range(1, len(subcodes) -1, 2):
            res[subcodes[i].strip()] = subcodes[i+1].strip().replace("\n", " ")
            # res.append({subcodes[i].strip(): subcodes[i+1].strip().replace("\n", " ")})
        return res
    def process_record(self, patient, data):

        if patient[0] == '1666':
            print(data)
        m = re.search(r'TOTALS\sFOR\sCLAIM\sNUMBER\s(\S+)', data)
        claim_number = m.group(1)

        m = re.match(r'^([0-9]+)\n(.+)$', data, re.DOTALL)
        ssn = m.group(1)
        rows = re.findall(r'[0-9]+\s[0-9]+\n[A-Z0-9]+\s[A-Z0-9]+\n[0-9]+\n[0-9\.\,]+\n[0-9\.\,]+\n(?:[0-9A-Z]+)?\n?[0-9\,]+\n[0-9\.\,]+\n[0-9\.\,]+\n[0-9\.\,]+\n(?:[0-9]+\n[0-9\.\,]+\n[0-9\.\,]+\n[0-9\.\,]+\n[0-9\.\,]+\n[0-9\.\,]+\n[0-9\.\,]+\n)*', m.group(2))
        m = re.search(r'LESS\sPREVIOUS\sPAYMENT\n(.+)\n', data)
        if m is not None:
            section_adjustment = locale.atof(m.group(1).strip())
        else:
            section_adjustment = 0
        for r in rows:
            self.process_row(patient, claim_number, r, section_adjustment)

    def process_pages(self, doc):
        patient_records = ''

        for page in doc.pages():
            patient_records = patient_records + page.getText("text", clip=fitz.Rect(160,0,594,700))
        
        temp = patient_records
        # print(patient_records)
        patient_records = re.findall(r'([0-9]+\n[0-9]+\s[0-9]+\n[A-Z0-9]+\s[A-Z0-9]+\n[0-9]+[^\']+)PATIENT\'S\sRESPONSIBILITY', patient_records, re.DOTALL)
        m = re.search(r'TRICARE\nPayment\n([0-9\.\,]+)\n([0-9\.\,]+)\n([0-9\.\,]+)\n([0-9\.\,]+)\n([0-9\.\,]+)\n([0-9\.\,]+)\nTRICARE Payment\n', temp)
        if m is not None:
            self.deductible = m.group(5)

        if(len(patient_records) < 1):
            return
        patients = ''
        for page in doc.pages():
            patients = patients + page.getText("text", clip=fitz.Rect(160,700,567,792))

        # print(patients)

        patients = [[x[0], x[1].replace("\n", " ").strip()] for x in re.findall(r'([0-9]+)\n([A-Z\s\n]+)', patients)]

        for p, r in zip(patients, patient_records):
            self.process_record(p, r)

with Bot() as scraper:
    # scraper.browser_init()
    scraper.main()
