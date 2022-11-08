import pandas as pd
import os
import requests
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.action_chains import ActionChains 
import time
import csv
import random
import logging
from PIL import Image
from webdriver_manager.firefox import GeckoDriverManager


class Bot:
    def __init__(self):
        self.url = "https://infocenter.humana-military.com/provider/service/Account/Login"
        self.search_url = "https://infocenter.humana-military.com/provider/service/"
        self.username = 'homefrontpumpse1'
        self.pw = 'HFPksv6220!@#'
        self.metabase_url = "http://metabase-izk7e-env.us-east-1.elasticbeanstalk.com/public/question/28f0fdde-3733-4881-87dc-94b78ed51c23.json"
        self.api_key = "2c00cd3434f14892b5372c24a9581946"
        self.post_url = "http://dmez.us-east-1.elasticbeanstalk.com/api/customers-payers/verify.json?api_key={}".format(self.api_key)
        self.abs_path = os.path.abspath(os.path.dirname(__file__))
        self.pdf_path = ''

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
        binary = FirefoxBinary('/usr/bin/firefox-esr')
        # binary = FirefoxBinary("C:\\Program Files\\Mozilla Firefox\\firefox.exe")
        drive = webdriver.Firefox(firefox_binary=binary, executable_path=GeckoDriverManager().install(), options=options)
        drive.get(self.url)
        drive.set_window_size(1440, 1440)
        iwait = random.randint(3, 4) + random.random()
        time.sleep(iwait)
        user_name = drive.find_element_by_id('txtUserId')
        user_name.send_keys(self.username)
        iwait = random.randint(3, 4) + random.random()
        time.sleep(iwait)
        password = drive.find_element_by_id('txtPassword')
        password.send_keys(self.pw)
        iwait = random.randint(3, 4) + random.random()
        time.sleep(iwait)
        login_button = drive.find_element_by_id('btnLogIn')
        drive.execute_script("arguments[0].click();", login_button)
        iwait = random.randint(10, 15) + random.random()
        time.sleep(iwait)
        self.drive = drive
    
    def get_metabase(self):
        metabase_json = requests.get(self.metabase_url).json()
        logging.warning("The metabase has {} patients info.".format(len(metabase_json)))
        return metabase_json
    
    def get_dob(self, customer_dob):
        dob = ""
        tmp = customer_dob.split('T')[0].split('-')
        dob = tmp[1] + '/' + tmp[2] + '/' + tmp[0]
        return dob

    def check_tricare_east(self, patient):
        print(patient)
        drive = self.drive
        drive.get(self.search_url)
        iwait = random.randint(15, 20) + random.random()
        time.sleep(iwait)
        payload = {}
        patient_dob = self.get_dob(patient['customer_dob'])
        img_tmp = 'tmpimg_' + str(patient['customers_payers_id']) + '-' + str(patient['order_id']) + '-' + time.strftime('%Y%m%d')

        if (len(patient['member_number']) == 10):
            patient['member_number'] = '0' + str(patient['member_number'])

        try:
            tricate_id = drive.find_element_by_id("txtTricareID1").send_keys(patient['member_number'])
        except Exception as e:
            drive.refresh
            iwait = random.randint(3, 5) + random.random()
            time.sleep(iwait)
            drive.get(self.search_url)
            iwait = random.randint(12, 15) + random.random()
            time.sleep(iwait)
            patient_dob = self.get_dob(patient['customer_dob'])
            tricate_id = drive.find_element_by_id("txtTricareID1").send_keys(patient['member_number'])

        tricate_dob = drive.find_element_by_id("txtDateOfBirth1").send_keys(patient_dob)

        payload['customers_payers_id'] = patient['customers_payers_id']
        payload['order_id'] = patient['order_id']

        try:
            view_button = drive.find_element_by_id("viewBeneficiaryProfileLink").click()
            iwait = random.randint(5, 8) + random.random()
            time.sleep(iwait)

            try:
                obj = drive.switch_to.alert
                message=obj.text
                print ("Alert shows following message: "+ message )
                obj.accept()
                iwait = random.randint(5, 8) + random.random()
                time.sleep(iwait)
            except Exception as e:
                pass

            drive.execute_script("window.scrollTo(0, 100)")
            iwait = random.randint(2, 3) + random.random()
            time.sleep(iwait)

            try:
                patient_info_view = requests.get("http://dmez.us-east-1.elasticbeanstalk.com/api/customers-payers/view/{}.json?api_key={}".format(patient['customers_payers_id'], self.api_key)).json()
                
                patient_first_name = patient_info_view["customersPayer"]["customer"]["firstname"]
                patient_last_name = patient_info_view["customersPayer"]["customer"]["lastname"]
                print(patient_first_name)
                print(patient_last_name)
                patient_links = drive.find_elements_by_xpath("//div[@id='divPatientList']/div[@class='k-grid-content']/table/tbody/tr/td/a")
                for patient_link in patient_links:
                    print(patient_link.text)
                    if (patient_first_name in patient_link.text) or (patient_last_name in patient_link.text):
                        action = ActionChains(drive) 
                        action.click(on_element = patient_link) 
                        action.perform()
                        iwait = random.randint(15, 18) + random.random()
                        time.sleep(iwait)
                        break

            except Exception as e:
                logging.warning('impossible to find patient lists.')
                logging.warning(e)

            drive.save_screenshot(self.abs_path + "/" + img_tmp + 'te1.png')
            iwait = random.randint(2, 3) + random.random()
            time.sleep(iwait)
            drive.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            drive.save_screenshot(self.abs_path + "/" + img_tmp + 'te2.png')
            iwait = random.randint(2, 3) + random.random()
            time.sleep(iwait)

            patient_info = drive.find_element_by_id("patientInfoData").text.split('\n')
            try:
                payload["eligibility_status"] = drive.find_element_by_xpath("//label[@for='PatientInfo_EligibilityStatus']/parent::div/following::div[@class='patientInfoDataRight']").text
            except Exception as e:
                payload["eligibility_status"] = ""
            payload['plan'] = ""
            payload['beneficiary_name'] = patient_info[2]
            payload['patient_address'] = patient_info[3]
            payload['relationship'] = ""
            try:
                payload["date_of_birth"] = drive.find_element_by_xpath("//label[@for='PatientInfo_DateOfBirth']/parent::div/following::div[@class='patientInfoDataRight']").text
            except Exception as e:
                payload["date_of_birth"] = ""
            try:
                payload["sponsor_name"] = drive.find_element_by_xpath("//label[@for='SponsorInfo_SponsorName']/parent::div/following::div[@class='sponsorInfoDataRight']").text
            except Exception as e:
                payload["sponsor_name"] = ""
            try:
                payload["sponsor_status"] = drive.find_element_by_xpath("//label[@for='SponsorInfo_Status']/parent::div/following::div[@class='sponsorInfoDataRight']").text
            except Exception as e:
                payload["sponsor_status"] = ""
            try:
                payload["sponsor_branch"] = drive.find_element_by_xpath("//label[@for='SponsorInfo_Branch']/parent::div/following::div[@class='sponsorInfoDataRight']").text
            except Exception as e:
                payload["sponsor_branch"] = ""
            try:
                payload["sponsor_rank"] = drive.find_element_by_xpath("//label[@for='SponsorInfo_RankAndGrade']/parent::div/following::div[@class='sponsorInfoDataRight']").text
            except Exception as e:
                payload["sponsor_rank"] = ""
            try:
                payload["military_base"] = drive.find_element_by_xpath("//label[@for='SponsorInfo_MilitaryBase']/parent::div/following::div[@class='sponsorInfoDataRight']").text
            except Exception as e:
                payload["military_base"] = ""
            try:
                payload["region"] = drive.find_element_by_xpath("//label[@for='SponsorInfo_Region']/parent::div/following::div[@class='sponsorInfoDataRight']").text
            except Exception as e:
                payload["region"] = ""
            effective = drive.find_element_by_id("fiscalDate").text.split('(')[-1].split(')')[0].split(' - ')
            payload['effective_date'] = effective[0]
            payload['end_date'] = effective[1]

            try:
                pos = drive.find_element_by_id("planYearAmountsPerPlanType").text.split('\n')
                payload['network_individual_deductible_met'] = pos[2].split(' ')[1]
                payload['network_individual_deductible_max'] = pos[2].split(' ')[2]
                payload['network_family_deductible_met'] = pos[3].split(' ')[1]
                payload['network_family_deductible_max'] = pos[3].split(' ')[2]
            except Exception as e:
                payload['network_individual_deductible_met'] = ""
                payload['network_individual_deductible_max'] = ""
                payload['network_family_deductible_met'] = ""
                payload['network_family_deductible_max'] = ""
            payload['non_network_individual_deductible_met'] = ""
            payload['non_network_individual_deductible_max'] = ""
            payload['non_network_family_deductible_met'] = ""
            payload['non_network_family_deductible_max'] = ""

            try:
                catastrophic = drive.find_element_by_id("planYearAmountsCap").text.split('\n')
                payload['individual_catastrophic_cap_met'] = catastrophic[2].split(' ')[1]
                payload['individual_catastrophic_cap_max'] = catastrophic[2].split(' ')[2]
                payload['family_catastrophic_cap_met'] = catastrophic[3].split(' ')[1]
                payload['family_catastrophic_cap_max'] = catastrophic[3].split(' ')[2]
            except Exception as e:
                payload['individual_catastrophic_cap_met'] = ""
                payload['individual_catastrophic_cap_max'] = ""
                payload['family_catastrophic_cap_met'] = ""
                payload['family_catastrophic_cap_max'] = ""
            payload['parse_error'] = 0

            try:
                drive.find_element_by_id("tricareRegionMap1").click()
                iwait = random.randint(2, 3) + random.random()
                time.sleep(iwait)
                drive.save_screenshot(self.abs_path + "/" + img_tmp + 'te3.png')
                iwait = random.randint(2, 3) + random.random()
                time.sleep(iwait)
                ohi_obj_list = drive.find_elements_by_xpath("//div[@id='divOHI']/div[@class='k-grid-content']/table/tbody/tr/td")
                ohi = []
                print(len(ohi_obj_list))
                for ohi_obj in ohi_obj_list:
                    ohi.append(ohi_obj.text)

                print(ohi)
                payload['other_health_insurance'] = {
                    'insurance_type': str(ohi[0]), 
                    'effective_date': str(ohi[1]),
                    'end_date': str(ohi[2]),
                    'coverage_type': str(ohi[3]),
                    'carrier_name': str(ohi[4]),
                    'policy_id': str(ohi[5])}
            except Exception as e:
                payload['other_health_insurance'] = {}

            payload['coverage_history'] = []
            try:
                coverages = drive.find_elements_by_xpath("//div[@id='divCoverageHistory']/div/table/tbody/tr/td")
                ran_max = len(coverages) / 5
                idx = 0
                for i in range(int(ran_max)):
                    cov = {}
                    cov["status"] = coverages[idx].text
                    cov["plan"] = coverages[idx + 1].text
                    cov["start_date"] = coverages[idx + 2].text
                    cov["end_date"] = coverages[idx + 3].text
                    cov["end_reason"] = coverages[idx + 4].text
                    payload['coverage_history'].append(cov)
                    idx = idx + 5
            except Exception as e:
                print(e)
                logging.warning('error in coverage history parsing')
            self.pdf_path = self.abs_path + "/" + str(payload['customers_payers_id']) + '-' + str(payload['order_id']) + '-' + time.strftime('%Y%m%d') + '.pdf'
        except Exception as e:
            payload['parse_error'] = 1
        final_payload = {'payload': payload,
                         'pdf_path': self.pdf_path,
                         'img_tmp': img_tmp}

        return final_payload

    def post_info_to_dmez(self, payload):
        try:
            files=[('pdf', open(self.pdf_path,'rb'))]
        except Exception as e:
            files=[('pdf', None)]
        headers = {'Cookie': 'CAKEPHP=3b653b4a5bce6ae92bd6d1ca71ca16d9'}
        response = requests.request("POST", self.post_url, headers=headers, data=payload, files=files)
        try:
            os.remove(self.abs_path + "/" + 'screenshotte1.png')
        except Exception as e:
            pass
        try:
            os.remove(self.abs_path + "/" + 'screenshotte2.png')
        except Exception as e:
            pass
        try:
            os.remove(self.abs_path + "/" + 'screenshotte3.png')
        except Exception as e:
            pass
        try:
            os.remove(self.pdf_path)
        except Exception as e:
            pass
        print('++++++++++++++++++++++++++++++++++++++++++++++++++++')
        print(response.text)
        print('++++++++++++++++++++++++++++++++++++++++++++++++++++')

    def main(self):
        metabase_json = self.get_metabase()
        for patient in metabase_json:
            if patient['payer_id'] == 1:
                self.post_info_to_dmez(self.check_tricare_east(patient))


# with Bot() as scraper:
#     scraper.browser_init()
#     scraper.main()