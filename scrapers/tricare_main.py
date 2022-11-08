import pandas as pd
import os
import requests
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time
import csv
import random
import logging
from PIL import Image
import json

from tricare_west import Bot as triwest
from tricare_east import Bot as trieast


api_key = "2c00cd3434f14892b5372c24a9581946"
post_url = "http://dmez.us-east-1.elasticbeanstalk.com/api/customers-payers/verify.json?api_key={}".format(api_key)
abs_path = os.path.abspath(os.path.dirname(__file__))
metabase_url = "http://metabase-izk7e-env.us-east-1.elasticbeanstalk.com/public/question/28f0fdde-3733-4881-87dc-94b78ed51c23.json"


def post_info_to_dmez(payload, pdf_path, tmp_img):
    try:
        image1 = Image.open(abs_path + "/" + tmp_img + "te1.png")
        im1 = image1.convert('RGB')
        image2 = Image.open(abs_path + "/" + tmp_img + "te2.png")
        im2 = image2.convert('RGB')
    except Exception as e:
        logging.warning('screenshotte2.png error')
    try:
        image3 = Image.open(abs_path + "/" + tmp_img + "te3.png")
        im3 = image3.convert('RGB')
    except Exception as e:
        logging.warning('screenshotte3.png error')

    try:
        image4 = Image.open(abs_path + "/" + tmp_img + "tw0.png")
        im4 = image4.convert('RGB')
    except Exception as e:
        logging.warning('screenshottw0.png error')
    try:
        image5 = Image.open(abs_path + "/" + tmp_img + "tw1.png")
        im5 = image5.convert('RGB')
    except Exception as e:
        logging.warning('screenshottw1.png error')
    try:
        im1.save(pdf_path, save_all=True, append_images=[im2, im3, im4, im5])
    except Exception as e:
        try:
            im1.save(pdf_path, save_all=True, append_images=[im2, im4, im5])
        except Exception as e1:
            logging.warning(e1)
    try:
        files = [('pdf', open(pdf_path, 'rb'))]
    except Exception as e:
        files = [('pdf', None)]
        return
    headers = {'Cookie': 'CAKEPHP=3b653b4a5bce6ae92bd6d1ca71ca16d9'}
    response = requests.request("POST", post_url, headers=headers, data=payload, files=files)
    try:
        for fname in os.listdir(abs_path):
            if 'tmpimg_' in fname:
                print(fname)
                os.remove(abs_path + "/" + fname)
    except Exception as e:
        pass
    try:
        os.remove(pdf_path)
    except Exception as e:
        pass
    print('++++++++++++++++++++++++++++++++++++++++++++++++++++')
    print(response.text)
    print('++++++++++++++++++++++++++++++++++++++++++++++++++++')


def get_metabase():
    metabase_json = requests.get(metabase_url).json()
    logging.warning("The metabase has {} patients info.".format(len(metabase_json)))
    return metabase_json


def conv_date(str_date):
    try:
        ary = str_date.split('/')
        return ary[2] + "-" + ary[0] + "-" + ary[1]
    except Exception as e:
        return ""

def conv2float(price):
    try:
        tmp = price.replace("$", "").replace(",", "").replace("-", "0")
        f_price = float(tmp)
        return f_price
    except Exception as e:
        return float(0)


def return_checked_merged(merged, main, passive):
    for key in merged.keys():
        try:
            if merged[key] == '' or merged[key] == {} or merged[key] == []:
                merged[key] = main[key]
        except Exception as e:
            pass
        try:
            if merged[key] == '' or merged[key] == {} or merged[key] == []:
                merged[key] = passive[key]
        except Exception as e:
            pass
    return merged


metabase_json = get_metabase()
for patient in metabase_json:
    if patient['payer_id'] == 3:
        continue
    if patient['payer_id'] == 0:
        continue
    print(patient)
    if patient['member_number'] == None:
        continue



    try:
        for fname in os.listdir(abs_path):
            if 'tmpimg_' in fname:
                print(fname)
                os.remove(abs_path + "/" + fname)
    except Exception as e:
        pass
    try:
        if patient['member_number'] == '':
            continue
    except Exception as e:
        continue
    with trieast() as eastbot:
        eastbot.browser_init()
        payload_east = eastbot.check_tricare_east(patient)
        print('====================')
        print(payload_east)
    with triwest() as westbot:
        westbot.browser_init()
        payload_west = westbot.check_tricare_west(patient)
        print('====================')
        print(payload_west)
        print('====================')
    c = {}
    if patient['payer_id'] == 1:
        overwrt = dict(payload_west["payload"], **payload_east["payload"])
        c = return_checked_merged(overwrt, payload_east["payload"], payload_west["payload"])
        
    elif patient['payer_id'] == 2:
        overwrt  = dict(payload_east["payload"], **payload_west["payload"])
        c = return_checked_merged(overwrt, payload_west["payload"], payload_east["payload"])

    c["effective_date"] = conv_date(c["effective_date"])
    c["end_date"] = conv_date(c["end_date"])

    try:
        c["date_of_birth"] = conv_date(c["date_of_birth"])
    except Exception as e:
        c["date_of_birth"] = ""
        pass
    
    try:
        for i in range(len(c["coverage_history"])):
            c["coverage_history"][i]["start_date"] = conv_date(c["coverage_history"][i]["start_date"])
            c["coverage_history"][i]["end_date"] = conv_date(c["coverage_history"][i]["end_date"])
    except Exception as e:
        c["coverage_history"] = ""
        pass
    c["coverage_history"] = json.dumps(c["coverage_history"])
    c["network_individual_deductible_met"] = conv2float(c["network_individual_deductible_met"])
    c["network_individual_deductible_max"] = conv2float(c["network_individual_deductible_max"])
    c["network_family_deductible_met"] = conv2float(c["network_family_deductible_met"])
    c["network_family_deductible_max"] = conv2float(c["network_family_deductible_max"])
    c["non_network_individual_deductible_met"] = conv2float(c["non_network_individual_deductible_met"])
    c["non_network_individual_deductible_max"] = conv2float(c["non_network_individual_deductible_max"])
    c["non_network_family_deductible_met"] = conv2float(c["non_network_family_deductible_met"])
    c["non_network_family_deductible_max"] = conv2float(c["non_network_family_deductible_max"])
    c["individual_catastrophic_cap_met"] = conv2float(c["individual_catastrophic_cap_met"])
    c["individual_catastrophic_cap_max"] = conv2float(c["individual_catastrophic_cap_max"])
    c["family_catastrophic_cap_met"] = conv2float(c["family_catastrophic_cap_met"])
    c["family_catastrophic_cap_max"] = conv2float(c["family_catastrophic_cap_max"])

    print(c)
    if c['eligibility_status'] == 'Unable to retrieve information':
        print('Error: Tricare East Error!!!.')
        break
    if c['parse_error'] == '1}':
        print('Error: PArse Error!!!.')
        continue

    post_info_to_dmez(c, payload_west["pdf_path"], payload_west["img_tmp"])