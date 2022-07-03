import time
import os
import re
import requests

from bot import APPDRIVE_EMAIL, APPDRIVE_PASSWORD, GDRIVE_FOLDER_ID

try: from lxml import etree
except:
   os.system("pip install lxml")
   from lxml import etree
try: from urllib.parse import urlparse
except:
   os.system("pip install urllib")
   from urllib.parse import urlparse
try: import cloudscraper
except:
   os.system("pip install cloudscraper") 
   import cloudscraper  
try: from bs4 import BeautifulSoup
except:
   os.system("pip install beautifulsoup4")
   from bs4 import BeautifulSoup


def get_gp_link(url: str):
    client = cloudscraper.create_scraper(allow_brotli=False)
    p = urlparse(url)
    final_url = f'{p.scheme}://{p.netloc}/links/go'

    res = client.head(url)
    header_loc = res.headers['location']
    param = header_loc.split('postid=')[-1]
    req_url = f'{p.scheme}://{p.netloc}/{param}'

    p = urlparse(header_loc)
    ref_url = f'{p.scheme}://{p.netloc}/'

    h = { 'referer': ref_url }
    res = client.get(req_url, headers=h, allow_redirects=False)

    bs4 = BeautifulSoup(res.content, 'html.parser')
    inputs = bs4.find_all('input')
    data = { input.get('name'): input.get('value') for input in inputs }

    h = {
        'referer': ref_url,
        'x-requested-with': 'XMLHttpRequest',
    }
    time.sleep(10)
    res = client.post(final_url, headers=h, data=data)
    try:
        return res.json()['url'].replace('\/','/')
    except:
        return False





# Website User Account (NOT GOOGLE ACCOUNT) ----
account = {
    'email': APPDRIVE_EMAIL, 
    'passwd': APPDRIVE_PASSWORD
}

# Destination config ----
SHARED_DRIVE_ID = GDRIVE_FOLDER_ID # team drive ID (optional) (for MyDrive, keep this field empty)
FOLDER_ID = '' # drive folder ID (optional)

'''
NOTE: 
 - Auto-detection for non-login urls, and indicated via 'link_type' (direct/login) in output.
SUPPORTED DOMAINS:
 - appdrive.in
 - driveapp.in
 
'''

# ===================================================================

def account_login(client, url, email, password):
    data = {
        'email': email,
        'password': password
    }
    client.post(f'https://{urlparse(url).netloc}/login', data=data)

def update_account(client, url, shared_drive_id, folder_id):
    data = {
        'root_drive': shared_drive_id,
        'folder': folder_id
    }
    client.post(f'https://{urlparse(url).netloc}/account', data=data)

def gen_payload(data, boundary=f'{"-"*6}_'):
    data_string = ''
    for item in data:
        data_string += f'{boundary}\r\n'
        data_string += f'Content-Disposition: form-data; name="{item}"\r\n\r\n{data[item]}\r\n'
    data_string += f'{boundary}--\r\n'
    return data_string

def parse_info(data):
    info = re.findall('>(.*?)<\/li>', data)
    info_parsed = {}
    for item in info:
        kv = [s.strip() for s in item.split(':', maxsplit = 1)]
        info_parsed[kv[0].lower()] = kv[1]
    return info_parsed

# ===================================================================

def appdrive_dl(url):
    client = requests.Session()
    client.headers.update({
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
    })

    account_login(client, url, account['email'], account['passwd'])
    update_account(client, url, SHARED_DRIVE_ID, FOLDER_ID)

    res = client.get(url)
    key = re.findall('"key",\s+"(.*?)"', res.text)[0]

    ddl_btn = etree.HTML(res.content).xpath("//button[@id='drc']")

    info_parsed = parse_info(res.text)
    info_parsed['error'] = False
    info_parsed['link_type'] = 'login' # direct/login
    
    headers = {
        "Content-Type": f"multipart/form-data; boundary={'-'*4}_",
    }
    
    data = {
        'type': 1,
        'key': key,
        'action': 'original'
    }
    
    if len(ddl_btn):
        info_parsed['link_type'] = 'direct'
        data['action'] = 'direct'
    
    while data['type'] <= 3:
        try:
            response = client.post(url, data=gen_payload(data), headers=headers).json()
            break
        except: data['type'] += 1
        
    if 'url' in response:
        info_parsed['gdrive_link'] = response['url']
    elif 'error' in response and response['error']:
        info_parsed['error'] = True
        info_parsed['error_message'] = response['message']
    else:
        info_parsed['error'] = True
        info_parsed['error_message'] = 'Something went wrong :('
    
    if info_parsed['error']: return info_parsed
    
    if urlparse(url).netloc == 'driveapp.in' and not info_parsed['error']:
        res = client.get(info_parsed['gdrive_link'])
        drive_link = etree.HTML(res.content).xpath("//a[contains(@class,'btn')]/@href")[0]
        info_parsed['gdrive_link'] = drive_link
        
    info_parsed['src_url'] = url
    
    return info_parsed
