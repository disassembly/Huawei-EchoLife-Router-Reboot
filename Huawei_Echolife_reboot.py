#!/usr/bin/env python3

"""
    A python 3 script to reboot Safaricom Echolife routers.
    Tested on: Huawei HG8245H
    Author: e13olf
"""

import os
import sys
import re
import codecs
import argparse
import base64
import requests
import urllib3
urllib3.disable_warnings()

#User Input Args
def parse_args():
    parser = argparse.ArgumentParser(
           formatter_class=argparse.RawDescriptionHelpFormatter,
           epilog=''
           'Usage example:'
           './Huawei_Echolife_Reboot.py -u <username> -p <password>')
           

    parser.add_argument("-u", "--USER", help="Router_Admin username.")
    parser.add_argument("-p", "--PASS", help="Router_Admin password")
   

    args = parser.parse_args()
    return parser.parse_args()

RAND_COUNT_URL = 'https://192.168.100.1/asp/GetRandCount.asp'
LOGIN_URL = 'https://192.168.100.1/login.cgi'
DEVICE_URL = 'https://192.168.100.1/html/ssmp/reset/reset.asp'
REBOOT_URL = 'https://192.168.100.1/html/ssmp/devmanage/set.cgi'

REBOOT_PARAMS = {'x': 'InternetGatewayDevice.X_HW_DEBUG.SMP.DM.ResetBoard',
                 'RequestFile': 'html/ssmp/reset/reset.asp'}

HW_TOKEN_PATTERN = r'id="hwonttoken" value="(\w+)">'

COOKIE_DEFAULT = {'Cookie': 'body:Language:english:id=1'}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,ja;q=0.6,de;q=0.5,fr',
    'Referer': 'http://192.168.100.1/index.asp',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1'
}


def cGet(url, params=None, **kwargs):
    return requests.get(url, params, headers=HEADERS, timeout=10, **kwargs)


def cPost(url, data=None, **kwargs):
    return requests.post(url, data, headers=HEADERS, timeout=10, **kwargs)

#Get hw token paramater from server
def getToken():
    r = cPost(RAND_COUNT_URL, verify=False, cookies=COOKIE_DEFAULT)
    if r.ok and r.text:
        return r.text[3:]
    else:
        print('Failed to get token, reason:', r.status_code)


#Login and retrive cookies
def login(user, passwd, token):
    username = user
    password = base64.b64encode(passwd.encode('utf-8')).decode("utf-8")
    print('Login using:', username, password)
    r = cPost(LOGIN_URL, verify=False, data={
        'UserName': username,
        'PassWord': password,
        'x.X_HW_Token': token
    }, cookies=COOKIE_DEFAULT)
    if r.ok and r.cookies:
        return r.cookies
    else:
        print('Failed to login: Invalid Creds?')


#Get hw token paramaters
def getHWToken(cookies):
    r = cGet(DEVICE_URL, verify=False, cookies=cookies)
    # print(r.request.headers)
    if r.ok:
        # print('hwonttoken' in r.text)
        m = re.search(HW_TOKEN_PATTERN, r.text)
        if m and m.group(1):
            return m.group(1)
        else:
            print('Failed to get hw token, reason:', r.status_code)


#Reboot device using cookies and hw token
def reboot(cookies, token):
    try:
        r = cPost(REBOOT_URL, params=REBOOT_PARAMS, verify=False, data={
            'x.X_HW_Token': token}, cookies=cookies)
        print(r.request.url)
        print(r.request.body)
        print(r.status_code)
        if r.ok:
            print('Rebooting...')
        else:
            print('Failed to reboot device.')
    except requests.exceptions.ReadTimeout as e:
        print('Rebooting...')
    except Exception as e:
        print('Failed to reboot device, reason:', e)

#Check user input_args        
def input_check(args):

    if not args.USER:
        exit('[!] ./Huawei_Echolife_Reboot.py -u <username> -p <password>\n')

    if not args.PASS:
        exit('[!] ./Huawei_Echolife_Reboot.py -u <username> -p <password>\n')


# Main Function
def doReboot(args):
    input_check(args)

    token = getToken()
    if not token:
        print('no token, abort')
        return
    print('Token:', token)
    cookies = login(args.USER, args.PASS, token)
    print('Cookies:', cookies)
    if not cookies:
        print('no cookies, abort.')
        return
    token = getHWToken(cookies)
    print('hwToken:', token)
    if not token:
        print('No hw token, abort.')
        return
    reboot(cookies, token)
    print('Device Rebooted!')


if __name__ == "__main__":
    doReboot(parse_args())
