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
        self.password = "!@#Hudspeth815"
        self.abs_path = os.path.abspath(os.path.dirname(__file__))
        self.doccount = 0
        self.records = []
        self.dateofnotice = ""
        self.checknumber = ""
        self.numericheader = ""
        self.summary = {}
        self.summary['Remark codes'] = []
        self.leftpatient = ''
        self.leftmedicare= ''
        self.posturl = "http://dmez.us-east-1.elasticbeanstalk.com/api/payments/frompayer.json?api_key=2c00cd3434f14892b5372c24a9581946"
        self.post_payer_id = '1'
        self.interest = 0
        self.patient_tot = 0
        self.total_amt = 0
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        try:
            x = 0
        except Exception as e:
            pass

    def main(self):
        # for i in range(12, 13):
            self.doccount = "2214834351"
            if os.path.exists(os.path.join(self.abs_path, str(self.doccount) + "east.pdf")):
                time.sleep(0.5)
                self.process_pdf()
                with open(os.path.join(self.abs_path, str(self.doccount) + "east.json"), "w") as outfile:
                    self.summary['Date of Notice'] = self.dateofnotice
                    self.summary['Check Number'] = self.checknumber
                    self.summary['NumericHeader']  = self.numericheader
                    json.dump({
                        "summary": self.summary,
                        "records": self.records
                    }, outfile)
                    self.records = []
                    self.summary = {}
                    self.dateofnotice = ""
                self.post_info_to_dmez( str(self.doccount) + "east.pdf",  str(self.doccount) + "east.json")

    def post_info_to_dmez(self, pdf_path, json_path):
        payload={ 'payer_id': self.post_payer_id }
        
        pdf_file = open(os.path.join(self.abs_path, pdf_path), 'rb')
        json_file = open(os.path.join(self.abs_path, json_path), 'rb')

        files=[
            ('pdf',(pdf_path, pdf_file ,'application/pdf')),
            ('json',(json_path, json_file,'application/json'))
        ]
        headers = {
            'Cookie': 'CAKEPHP=805b5cd5a6fd02f607da0921b49639ca'
        }

        response = requests.request("POST", self.posturl, headers=headers, data=payload, files=files)
        print(response.text)

    def process_pdf(self):
        try:
            doc = fitz.open(os.path.join(self.abs_path, str(self.doccount) + "east.pdf"))
            self.addr = doc[0].getText("text", clip=fitz.Rect(60,144,190,200))

            self.process_pages(doc)
            # for p in doc.pages():
            #     self.process_page(p)
            doc.close()
            print("Total Amount {}".format(self.total_amt))
        except Exception as e:
            print(str(e))
            pass
    def process_services(self, data):
        services = re.findall(r'(\d\d/\d\d/\d\d-\d\d/\d\d/\d\d)\n([^\n]+\n)([^\n]+\n)([^\n]+\n)([^\n]+\n)([^\n]+\n)([^\n]+\n)([^\n]+\n)([^\n]+\n)', data, re.DOTALL)
        totalinfo = re.sub(r'(\d\d/\d\d/\d\d-\d\d/\d\d/\d\d)\n([^\n]+\n)([^\n]+\n)([^\n]+\n)([^\n]+\n)([^\n]+\n)([^\n]+\n)([^\n]+\n)([^\n]+\n)', '', data)

        details = []
        for service in services:
            details.append({
                "Date of Service" : service[0].strip('$\n'),
                "Procedure" : service[1].strip().split(' ')[0],
                "Mod" : service[1].strip().split(' ')[1],
                "No" : service[2].strip('$\n'),
                "Billed" : locale.atof(service[3].strip('$\n')),
                "Allowed" : locale.atof(service[4].strip('$\n')),
                "Deduct" : locale.atof(service[5].strip('$\n')),
                "Cost-share" : locale.atof(service[6].strip('$\n')),
                "Code" :service[7].strip('$\n'),
                "Paid" : locale.atof(service[8].strip('$\n')),        
            })
            self.patient_tot = self.patient_tot + locale.atof(service[8].strip('$\n'))

        self.interest = 0
        if totalinfo.find('Interest Paid:') >= 0:            
            m = re.search(r'Interest\sPaid:\n(\$[\d.,]+\n)', totalinfo, re.DOTALL)
            self.interest = locale.atof(m.group(1).strip('$\n'))
            self.patient_tot = self.patient_tot + self.interest

        totalinfo = re.search(r'PT\sResp\n(\$[\d.,]+\n)Claim\sTotals\n(\$[\d.,]+\n)(\$[\d.,]+\n)(\$[\d.,]+\n)(\$[\d.,]+\n)(\$[\d.,]+)', totalinfo, re.DOTALL)
        res = []
        for i in range(0, len(details)):
            res.append({
                    "RT Resp": locale.atof(totalinfo.group(1).strip('$\n')),
                    "Total Billed" : locale.atof(totalinfo.group(2).strip('$\n')),
                    "Total Allowed" : locale.atof(totalinfo.group(3).strip('$\n')),
                    "Total Deduct" : locale.atof(totalinfo.group(4).strip('$\n')),
                    "Total Cost-share" : locale.atof(totalinfo.group(5).strip('$\n')),
                    "Total Paid": locale.atof(totalinfo.group(6).strip('$\n')),
                    "Details" : details[i],
                }
            )
            
        return res
    def process_out_of_pocket(self, data):
        m = re.match(r'\*Medicare/Other Ins.\sPaid\s(\$[\d.,]+)\n[^\d]+([^\n]+)\n([^\n]+)\n([^\n]+)\n([^\n]+)', data, re.DOTALL)   
        return {
            "*Medicare/Other Ins. Paid" : m.group(1).strip(),
            "Year" : m.group(2).strip(),
            "Catastrophic Cap Met to Date" : m.group(3).strip(),
            "Deductible - Individual" : m.group(4).strip(),
            "Deductible - Family" : m.group(5).strip()
        }
    def process_record(self, data):
        # m = re.match(r'Patient\sNumber:\s([^\n]+)\nClaim\sNumber:\s([^\n]+)\nCheck\sNumber:\s([^\n]+)\nSponsor\sNumber:\s([^\n]+)\nPatient\sName:\s([^\n]+)\nSponsor\sName:\s([^\n]+)\n([^\*]+)\n(.+)', data, re.DOTALL)      
        m = re.match(r'Patient\sNumber:(.+)Claim\sNumber:(.+)Check\sNumber:(.+)Sponsor\sNumber:(.+)Patient\sName:(.+)Sponsor\sName:\s([^\d]+)([^\*]+)\n(.+)', data, re.DOTALL)

        try:
            self.patient_tot = 0
            services = self.process_services(m.group(7))

            print("Patient Number {}   {}".format(m.group(1).strip(), self.patient_tot))
            self.total_amt = self.total_amt + self.patient_tot
            outofpocket = self.process_out_of_pocket(m.group(8))

            for i in range(0, len(services)):
                self.records.append({
                    "Patient Number": m.group(1).strip(),
                    "Claim Number" : m.group(2).strip(),
                    # "Check Number" : m.group(3).strip(),
                    "Sponsor Number" : m.group(4).strip(),
                    "Patient Name" : m.group(5).strip(),
                    "Sponsor Name" : m.group(6).strip(),
                    "Services" : services[i],
                    "Out of Pocket Expenses met to date" : outofpocket,
                    "adjustment" : self.interest if not self.interest == 0 else 0,
                    "adjustment_reason " : "Interest" if not self.interest == 0 else ""
                })
                if not self.interest == 0:
                    self.interest = 0
        except: 
            pass

    def process_pages(self, doc):

        page_content = ''
        page_content = doc[1].getText("text", clip=fitz.Rect(0,0,768,576))
        # print(page_content)
        if self.dateofnotice == "":
            # dateofnotice = re.findall(r'Date of Notice:\s[^\n]+', page_content, re.DOTALL)
            pageheader = re.findall(r'Date\sof\sNotice:([^\n]+)\nCEOB\sNumber:([^\n]+)\n', page_content, re.DOTALL)
            if len(pageheader) > 0:
                self.dateofnotice = pageheader[0][0].strip()
                self.numericheader = ''
                self.checknumber = pageheader[0][1].strip()
            else:
                pageheader = re.findall(r'Date of Notice:\s([^\n]+)\n([^\n]+)\n([^\n]+)\n', page_content, re.DOTALL)
                if len(pageheader) > 0:
                    self.dateofnotice = pageheader[0][0].strip()
                    self.numericheader = pageheader[0][1].strip()
                    self.checknumber = pageheader[0][2].strip()

        page_content = ''
        for page in doc.pages():
            page_content = page_content + page.getText("text", clip=fitz.Rect(0,60,768,576))

        # print(page_content)
        # patient_records = re.findall(r'Patient\sNumber:[^/]+[0-9/-]+[^\*]+[^\-]+\-[^\-]+\-\s[\w]+\n[^\n]+\n[^\n]+\n[^\n]+\n[^\n]+\n', page_content, re.DOTALL)
        patient_records = re.findall(r'Patient\sNumber:[^/]+[0-9/-]+[^\*]+', page_content, re.DOTALL)
        medicares = re.findall(r'\*Medicare[^\n]+\n[^\d]+\n[^\n]+\n[^\n]+\n[^\n]+\n[^\n]+\n', page_content, re.DOTALL)


        # IF Interest exists in Payment Summary
        m = re.findall(r'(Payment\sSummary:\n)(\$[\d\,\.]+\n)(\$[\d\,\.]+\n)(\$[\d\,\.]+\n)(\$[\d\,\.]+\n)(\$[\d\,\.]+\n)(\$[\d\,\.]+\n)', page_content, re.DOTALL)
        if len(m) > 0:
                self.summary['Payment Summary'] = {}
                self.summary['Payment Summary']['Billed'] = locale.atof(m[0][1].strip('$\n'))
                self.summary['Payment Summary']['Allowed'] = locale.atof(m[0][2].strip('$\n'))
                self.summary['Payment Summary']['Interest'] = locale.atof(m[0][3].strip('$\n'))
                self.summary['Payment Summary']['Total Payable'] = locale.atof(m[0][4].strip('$\n'))
                self.summary['Payment Summary']['Offset'] = locale.atof(m[0][5].strip('$\n'))
                self.summary['Payment Summary']['Net Amount Paid'] = locale.atof(m[0][6].strip('$\n'))
        else:
            m = re.findall(r'(Payment\sSummary:\n)(\$[\d\,\.]+\n)(\$[\d\,\.]+\n)(\$[\d\,\.]+\n)(\$[\d\,\.]+\n)(\$[\d\,\.]+\n)', page_content, re.DOTALL)
            if len(m) > 0:
                self.summary['Payment Summary'] = {}
                self.summary['Payment Summary']['Allowed'] = locale.atof(m[0][2].strip('$\n'))
                self.summary['Payment Summary']['Billed'] = locale.atof(m[0][1].strip('$\n'))
                self.summary['Payment Summary']['Total Payable'] = locale.atof(m[0][3].strip('$\n'))
                self.summary['Payment Summary']['Offset'] = locale.atof(m[0][4].strip('$\n'))
                self.summary['Payment Summary']['Net Amount Paid'] = locale.atof(m[0][5].strip('$\n'))


        try:
            m = re.findall(r'Remark\scodes:\n(.*)Important\smessages', page_content, re.DOTALL)
            if len(m) > 0:
                m[0]  = m[0].replace(':\n', ': ')
                m = re.findall(r'([^\n]+)', m[0], re.DOTALL)
                self.summary['Remark codes'] = {}
                
                lastcode = ""
                for line in m:
                    code = re.match(r'([\w]+)\:\s(.*)', line,  re.DOTALL)
                    if code is not None:
                        lastcode = code.group(1).strip()
                        self.summary['Remark codes'][lastcode] = code.group(2).strip()                    
                    else:
                        self.summary['Remark codes'][lastcode] += "\n" + line.strip()
            else:
                m = re.findall(r'Remark\scodes:\n(.*)Humana\sMilitary', page_content, re.DOTALL)
                if len(m) > 0:
                    m[0]  = m[0].replace(':\n', ': ')
                    m = re.findall(r'([^\n]+)', m[0], re.DOTALL)
                    self.summary['Remark codes'] = {}
                    
                    lastcode = ""
                    for line in m:
                        code = re.match(r'([\w]+)\:\s(.*)', line,  re.DOTALL)
                        if code is not None:
                            lastcode = code.group(1).strip()
                            self.summary['Remark codes'][lastcode] = code.group(2).strip()                    
                        else:
                            self.summary['Remark codes'][lastcode] += "\n" + line.strip()
                    
        except:
            pass

        m = re.findall(r'Important\smessages:\n(.*)', page_content, re.DOTALL)
        if len(m) > 0:

            msgs = m[0].strip().split('\n')
            self.summary['Important messages'] = []
            cnt = int(len(msgs)/2)
            for i in range(0, cnt):
                self.summary['Important messages'].append(
                    msgs[i * 2 + 1]
                )        
        patient_len = len(patient_records)
        medicare_len = len(medicares)

        if patient_len > 0 or medicare_len > 0:
            if self.leftpatient:
                patient_records.insert(0, self.leftpatient)
            if self.leftmedicare:
                medicares.insert(0, self.leftmedicare)

            patient_len = len(patient_records)
            medicare_len = len(medicares)
            total_cnt = min(patient_len, medicare_len)
            for i in range(0, total_cnt):
                self.process_record(patient_records[i] +  medicares[i])
            
            self.leftpatient = ''
            self.leftmedicare = ''
            if patient_len > medicare_len:
                self.leftpatient = patient_records[patient_len - 1]
            elif medicare_len > patient_len:
                self.leftmedicare = medicares[medicare_len - 1]

with Bot() as scraper:
    # scraper.browser_init()
    scraper.main()
