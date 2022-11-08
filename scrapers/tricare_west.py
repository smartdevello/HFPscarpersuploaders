import os
import requests
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import csv
import random
import logging
from PIL import Image


class Bot:
    def __init__(self):
        self.url = "https://www.tricare-west.com/idp/prov-login.fcc"
        self.username = 'homefrontpumpsw1'
        self.pw = 'Hudspeth815!@#'
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
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--ignore-certificate-errors')
        drive = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
        drive.get(self.url)
        iwait = random.randint(2, 3) + random.random()
        time.sleep(iwait)
        user_name = drive.find_element_by_id('username_bene')
        user_name.send_keys(self.username)
        password = drive.find_element_by_id('password_bene')
        password.send_keys(self.pw)
        iwait = random.randint(2, 3) + random.random()
        time.sleep(iwait)
        login_button = drive.find_element_by_id('prov-login').click()
        iwait = random.randint(4, 5) + random.random()
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
        payload = {}
        return payload


    def check_tricare_west(self, patient):
        print(patient)
        drive = self.drive
        payload = {}
        patient_dob = self.get_dob(patient['customer_dob'])
        tmp = ''
        if patient['member_number'][-1] == '0' and patient['member_number'][-2] == '0':
            tmp = patient['member_number'][:-1] + '1'
        print(tmp)
        img_tmp = 'tmpimg_' + str(patient['customers_payers_id']) + '-' + str(patient['order_id']) + '-' + time.strftime('%Y%m%d')
        url = "https://www.tricare-west.com/content/hnfs/home/tw/prov/secure/app-forms/ohi/search-ohi.html"
        drive.get(url)
        iwait = random.randint(5, 8) + random.random()
        time.sleep(iwait)

        try:
            drive.find_element_by_xpath("//a[@title='Click to close.']").click()
            iwait = random.randint(5, 8) + random.random()
            time.sleep(iwait)
        except Exception as e:
            pass

        DBN_checkbox = drive.find_element_by_id('searchUserOHIDBN').click()
        DBN_input = drive.find_element_by_id('patientDBN').send_keys(patient['member_number'])
        DOB_date = drive.find_element_by_id('dbnPatientDOBText').send_keys(patient_dob)
        iwait = random.randint(2, 3) + random.random()
        time.sleep(iwait)
        search_button = drive.find_elements_by_xpath("//form[@id='formSearchUserOHIDBN']/div/button")[0].click()
        iwait = random.randint(2, 3) + random.random()
        time.sleep(iwait)

        OHI = {}
        try:
            view_button = drive.find_element_by_id('views').click()
            iwait = random.randint(2, 3) + random.random()
            time.sleep(iwait)
            OHI['policyHolderName'] = drive.find_element_by_id('policyHolderName').text
            OHI['ohiInsuranceType'] = drive.find_element_by_id('ohiInsuranceType').text
            OHI['insuranceName'] = drive.find_element_by_id('insuranceName').text
            OHI['relationshipToPolicyHolder'] = drive.find_element_by_id('relationshipToPolicyHolder').text
            OHI['effectiveDate1'] = drive.find_element_by_id('effectiveDate1').text
            OHI['endDate1'] = drive.find_element_by_id('endDate1').text
            OHI['policyNumber'] = drive.find_element_by_id('policyNumber').text
            OHI['drugCoverage'] = drive.find_element_by_id('drugCoverage').text
            OHI['hmoppo'] = drive.find_element_by_id('hmoppo').text
            print(OHI)
            print('success in step 1')
        except Exception as e:
            if tmp is not '':
                drive.get(url)
                iwait = random.randint(2, 3) + random.random()
                time.sleep(iwait)
                try:
                    drive.find_element_by_xpath("//a[@title='Click to close.']").click()
                    iwait = random.randint(5, 8) + random.random()
                    time.sleep(iwait)
                except Exception as e:
                    pass
                drive.find_element_by_id('searchUserOHIDBN').click()
                drive.find_element_by_id('patientDBN').send_keys(tmp)
                drive.find_element_by_id('dbnPatientDOBText').send_keys(patient_dob)
                drive.find_elements_by_xpath("//form[@id='formSearchUserOHIDBN']/div/button")[0].click()
                iwait = random.randint(2, 3) + random.random()
                time.sleep(iwait)
                try:
                    drive.find_element_by_id('views').click()
                    iwait = random.randint(2, 3) + random.random()
                    time.sleep(iwait)
                    OHI['policyHolderName'] = drive.find_element_by_id('policyHolderName').text
                    OHI['ohiInsuranceType'] = drive.find_element_by_id('ohiInsuranceType').text
                    OHI['insuranceName'] = drive.find_element_by_id('insuranceName').text
                    OHI['relationshipToPolicyHolder'] = drive.find_element_by_id('relationshipToPolicyHolder').text
                    OHI['effectiveDate1'] = drive.find_element_by_id('effectiveDate1').text
                    OHI['endDate1'] = drive.find_element_by_id('endDate1').text
                    OHI['policyNumber'] = drive.find_element_by_id('policyNumber').text
                    OHI['drugCoverage'] = drive.find_element_by_id('drugCoverage').text
                    OHI['hmoppo'] = drive.find_element_by_id('hmoppo').text
                    print(OHI)
                    print('success in step 1-1')
                except Exception as e:
                    pass
        drive.set_window_size(1440, 1440)
        iwait = random.randint(2, 3) + random.random()
        time.sleep(iwait)
        drive.save_screenshot(self.abs_path + "/" + img_tmp + 'tw0.png')
        payload['other_health_insurance'] = OHI

        url = "https://www.tricare-west.com/content/hnfs/home/tw/prov/secure/app-forms/check-eligibility.html"
        drive.get(url)
        iwait = random.randint(10, 15) + random.random()
        time.sleep(iwait)
        try:
            drive.find_element_by_xpath("//a[@title='Click to close.']").click()
            iwait = random.randint(5, 8) + random.random()
            time.sleep(iwait)
        except Exception as e:
            pass


        DBN_checkbox = drive.find_element_by_id('HNFSCheckEligibilityDBNid').click()
        DBN_input = drive.find_element_by_id('dbnid1').send_keys(patient['member_number'])
        DOB_date = drive.find_element_by_id('dobDBNDate1').send_keys(patient_dob)
        search_button = drive.find_element_by_id('dbnSearch').click()
        iwait = random.randint(4, 5) + random.random()
        time.sleep(iwait)
        try:
            drive.execute_script("window.scrollTo(0, 500)")
            iwait = random.randint(2, 3) + random.random()
            time.sleep(iwait)
            drive.save_screenshot(self.abs_path + "/" + img_tmp + 'tw1.png')
            iwait = random.randint(2, 3) + random.random()
            time.sleep(iwait)
            
            payload['eligibility_status'] = drive.find_element_by_id('provDbnStatus').text
            payload['plan'] = drive.find_element_by_id('provDbnPlan').text
            payload['beneficiary_name'] = drive.find_element_by_id('provDbnHeading').text
            payload['relationship'] = drive.find_element_by_id('provDbnRelationship').text
            payload['region'] = drive.find_element_by_id('provDbnRegionType').text
            payload['effective_date'] = drive.find_element_by_id('provDbnSecEffDate').text
            payload['end_date'] = drive.find_element_by_id('provDbnSecEndDate').text
            payload['customers_payers_id'] = patient['customers_payers_id']
            payload['order_id'] = patient['order_id']
            payload['group_name'] = drive.find_element_by_id('provDbnGroup').text
            payload['sponsor_benefit_type'] = drive.find_element_by_id('provDbnSponsorType').text
            payload['gender'] = drive.find_element_by_id('provDbnGender').text
            payload['primary_care_manager_name'] = drive.find_element_by_id('provDbnManager').text
            payload['primary_care_manager_number'] = drive.find_element_by_id('provDbnManagerPhone').text
            payload['secondary_plan'] = drive.find_element_by_id('provDbnSecPlan').text
            payload['plan_year'] = drive.find_element_by_id('provDbnFiscalYear').text
            payload['network_individual_deductible_met'] = drive.find_element_by_id('provDbnIndDed').text.split(' / ')[0].replace('$', '')
            payload['network_individual_deductible_max'] = drive.find_element_by_id('provDbnIndDed').text.split(' / ')[-1].replace('$', '')
            payload['network_family_deductible_met'] = drive.find_element_by_id('provDbnFamDed').text.split(' / ')[0].replace('$', '')
            payload['network_family_deductible_max'] = drive.find_element_by_id('provDbnFamDed').text.split(' / ')[-1].replace('$', '')
            payload['non_network_individual_deductible_met'] = drive.find_element_by_id('provDbnIndDedNon').text.split(' / ')[0].replace('$', '')
            payload['non_network_individual_deductible_max'] = drive.find_element_by_id('provDbnIndDedNon').text.split(' / ')[-1].replace('$', '')
            payload['non_network_family_deductible_met'] = drive.find_element_by_id('provDbnFamDedNon').text.split(' / ')[0].replace('$', '')
            payload['non_network_family_deductible_max'] = drive.find_element_by_id('provDbnFamDedNon').text.split(' / ')[-1].replace('$', '')
            payload['individual_catastrophic_cap_met'] = drive.find_element_by_id('provDbnIndCatCap').text.split(' / ')[0].replace('$', '')
            payload['individual_catastrophic_cap_max'] = drive.find_element_by_id('provDbnIndCatCap').text.split(' / ')[-1].replace('$', '')
            payload['family_catastrophic_cap_met'] = drive.find_element_by_id('provDbnFamCatCap').text.split(' / ')[0].replace('$', '')
            payload['family_catastrophic_cap_max'] = drive.find_element_by_id('provDbnFamCatCap').text.split(' / ')[-1].replace('$', '')
            payload['parse_error'] = 0
            
            print('success in step 2')
        except Exception as e:
            if tmp is not '':
                drive.get(url)
                iwait = random.randint(2, 3) + random.random()
                time.sleep(iwait)

                drive.find_element_by_id('HNFSCheckEligibilityDBNid').click()
                drive.find_element_by_id('dbnid1').send_keys(tmp)
                drive.find_element_by_id('dobDBNDate1').send_keys(patient_dob)
                drive.find_element_by_id('dbnSearch').click()
                iwait = random.randint(4, 5) + random.random()
                time.sleep(iwait)
                try:
                    drive.execute_script("window.scrollTo(0, 500)")
                    iwait = random.randint(2, 3) + random.random()
                    time.sleep(iwait)
                    drive.save_screenshot(self.abs_path + "/" + img_tmp + 'tw1.png')
                    iwait = random.randint(2, 3) + random.random()
                    time.sleep(iwait)
                    
                    payload['eligibility_status'] = drive.find_element_by_id('provDbnStatus').text
                    payload['plan'] = drive.find_element_by_id('provDbnPlan').text
                    payload['beneficiary_name'] = drive.find_element_by_id('provDbnHeading').text
                    payload['relationship'] = drive.find_element_by_id('provDbnRelationship').text
                    payload['region'] = drive.find_element_by_id('provDbnRegionType').text
                    payload['effective_date'] = drive.find_element_by_id('provDbnSecEffDate').text
                    payload['end_date'] = drive.find_element_by_id('provDbnSecEndDate').text
                    payload['customers_payers_id'] = patient['customers_payers_id']
                    payload['order_id'] = patient['order_id']
                    payload['group_name'] = drive.find_element_by_id('provDbnGroup').text
                    payload['sponsor_benefit_type'] = drive.find_element_by_id('provDbnSponsorType').text
                    payload['gender'] = drive.find_element_by_id('provDbnGender').text
                    payload['primary_care_manager_name'] = drive.find_element_by_id('provDbnManager').text
                    payload['primary_care_manager_number'] = drive.find_element_by_id('provDbnManagerPhone').text
                    payload['secondary_plan'] = drive.find_element_by_id('provDbnSecPlan').text
                    payload['plan_year'] = drive.find_element_by_id('provDbnFiscalYear').text
                    payload['network_individual_deductible_met'] = drive.find_element_by_id('provDbnIndDed').text.split(' / ')[0].replace('$', '')
                    payload['network_individual_deductible_max'] = drive.find_element_by_id('provDbnIndDed').text.split(' / ')[-1].replace('$', '')
                    payload['network_family_deductible_met'] = drive.find_element_by_id('provDbnFamDed').text.split(' / ')[0].replace('$', '')
                    payload['network_family_deductible_max'] = drive.find_element_by_id('provDbnFamDed').text.split(' / ')[-1].replace('$', '')
                    payload['non_network_individual_deductible_met'] = drive.find_element_by_id('provDbnIndDedNon').text.split(' / ')[0].replace('$', '')
                    payload['non_network_individual_deductible_max'] = drive.find_element_by_id('provDbnIndDedNon').text.split(' / ')[-1].replace('$', '')
                    payload['non_network_family_deductible_met'] = drive.find_element_by_id('provDbnFamDedNon').text.split(' / ')[0].replace('$', '')
                    payload['non_network_family_deductible_max'] = drive.find_element_by_id('provDbnFamDedNon').text.split(' / ')[-1].replace('$', '')
                    payload['individual_catastrophic_cap_met'] = drive.find_element_by_id('provDbnIndCatCap').text.split(' / ')[0].replace('$', '')
                    payload['individual_catastrophic_cap_max'] = drive.find_element_by_id('provDbnIndCatCap').text.split(' / ')[-1].replace('$', '')
                    payload['family_catastrophic_cap_met'] = drive.find_element_by_id('provDbnFamCatCap').text.split(' / ')[0].replace('$', '')
                    payload['family_catastrophic_cap_max'] = drive.find_element_by_id('provDbnFamCatCap').text.split(' / ')[-1].replace('$', '')
                    payload['parse_error'] = 0
                    
                    print('success in step 2-2')
                except Exception as e:
                    payload['parse_error'] = 1
                    pass
            # print(e)
            pass
        
        self.pdf_path = self.abs_path + "/" + str(payload['customers_payers_id']) + '-' + str(payload['order_id']) + '-' + time.strftime('%Y%m%d') + '.pdf'
        # print(payload)
        final_payload = {'payload': payload,
                         'pdf_path': self.pdf_path,
                         'img_tmp': img_tmp}

        return final_payload
    
    def check_other_not_serviced(self, patient):
        payload = {}
        return payload

    def post_info_to_dmez(self, payload):
        print(self.pdf_path)
        files=[('pdf', open(self.pdf_path,'rb'))]
        headers = {'Cookie': 'CAKEPHP=3b653b4a5bce6ae92bd6d1ca71ca16d9'}
        response = requests.request("POST", self.post_url, headers=headers, data=payload, files=files)
        try:
            os.remove(self.abs_path + "/" + 'screenshottw0.png')
        except Exception as e:
            pass
        try:
            os.remove(self.abs_path + "/" + 'screenshottw1.png')
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
                continue
                self.post_info_to_dmez(self.check_tricare_east(patient))
            elif patient['payer_id'] == 2:
                self.post_info_to_dmez(self.check_tricare_west(patient))
            elif patient['payer_id'] == 3:
                continue
                self.post_info_to_dmez(self.check_other_not_serviced(patient))


# with Bot() as scraper:
#     scraper.browser_init()
#     scraper.main()