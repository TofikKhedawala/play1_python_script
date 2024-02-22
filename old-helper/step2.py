# from sheet_api import read_output_sheet_output,download_file_by_id,update_outputfile_insheet
# from googleapiclient.discovery import build
from .config import *
from .drive_upload import get_drive_link
from .helper import store_output
import pandas as pd
import concurrent.futures
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import re
import os
import csv
from validate_email import validate_email
import time
import json
from difflib import SequenceMatcher
import spacy

english_nlp = spacy.load('en_core_web_sm')

def give_notes(url, soup):
    note = ''
    # text = soup.get_text()
    # if 'board' in text:
    #     note += 'text contains word board '

    if ('news' in url) or ('media' in url):
        note += 'seems to be news website '
    return note

emails_validations = {}
def is_valid_email(email):
    if email in emails_validations:
        return emails_validations[email]
    try:
        is_valid = validate_email(email, check_format=True,check_blacklist=True,
        check_dns=True,dns_timeout=10,check_smtp=True,smtp_timeout=10)
        print('is valid',email,  is_valid)
        if is_valid == None:
            emails_validations[email] = True
            return True
        emails_validations[email] = is_valid
        return is_valid
    except Exception as e:
        print('error while validating mail', e)
        return False
    
def validate_emails_with_thread(email_list):
    print('validating email')
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Use list comprehension to apply the email validation function in parallel
        valid_emails = list(executor.map(is_valid_email, email_list))
    return valid_emails

def detectorgname(text):
    name = ''
    spacy_parser = english_nlp(text)
    for entity in spacy_parser.ents:
        # print(f'Found: {entity.text} of type: {entity.label_}')
        if (entity.label_ == 'ORG') and ('home' not in entity.text.lower()) and ('page' not in entity.text.lower()):
            name = entity.text
            break
    return name

def getHumanname(soup):
    names = []
    spacy_parser = english_nlp(soup.get_text())
    for entity in spacy_parser.ents:
        try:
            if len(names)>10:
                continue
            print(f'Found: {entity.text} of type: {entity.label_}')
            if (entity.label_ == 'PERSON') and ('loading' not in entity.text.lower()) and ('login' not in entity.text.lower()) and ('html' not in entity.text.lower()):
                names.append(entity.text)
        except Exception as e:
            print('error in getHumanname',e)
            continue
    return names

# Function to extract phone numbers and emails from text
def extract_contact_info(soup, link):
    startTime = time.time()
    print('scraping contact')
    mobile_pattern = r'\b(?:1-)?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    mobile_numbers = re.findall(mobile_pattern, soup.get_text())
    mobile_numbers = list(set(mobile_numbers)) #to remove dublicates
    if len(mobile_numbers)>10:
        mobile_numbers = mobile_numbers[:3] # if we got more than 10 email some thing is wrong give first 10 only


    # emails_from_text = re.findall(email_pattern, soup.get_text())
    emails_from_html = re.findall(email_pattern, soup.prettify())

    emails_from_html = [ i   for i in emails_from_html if '.png' not in i.lower() ]
    emails_from_html = [ i   for i in emails_from_html if '.jpg' not in i.lower() ]
    emails_from_html = [ i   for i in emails_from_html if '.svg' not in i.lower() ]
    emails_from_html = [ i   for i in emails_from_html if '.js' not in i.lower() ]
    emails_from_html = [ i   for i in emails_from_html if 'wixpress.com' not in i.lower() ]
    emails_from_html = list(set(emails_from_html)) #to remove dublicates  

    # using threading to verify emails
    print('email before filter from html ',emails_from_html,link, 'took ', time.time()-startTime )
    valid_emails_from_html = validate_emails_with_thread(emails_from_html)
    valid_emails = [email for email, is_valid in zip(emails_from_html, valid_emails_from_html) if is_valid]
    emails_from_html = valid_emails

    emails_from_html = list(filter(is_valid_email, emails_from_html))
    emails_from_html = emails_from_html[:10] # if we got more than 10 email some thing is wrong give first 10 only
    print('email after filter html ',emails_from_html,link, 'took ', time.time()-startTime )
    # print('email from text ',emails_from_text )
    notes = give_notes(link, soup)
    names=[]
    if len(mobile_numbers)!=0:
        names = getHumanname(soup)
    return mobile_numbers, emails_from_html,notes,names
  
def get_recursive_links(soup,domain):
    links = []
    all_a_tags = soup.findAll('a')
    
    # Loop through the <a> tags
    for a_tag in all_a_tags:
        # Get the text within the <a> tag
        link_text = a_tag.get_text()

        # Check if any of the keywords are in the link text
        if any(keyword.lower() in link_text.lower() for keyword in LINK_KEYWORDS):
            # If a keyword is found, print the link text and URL
            link_url = a_tag.get('href')
            if link_url:
                if domain in link_url:
                    links.append(link_url)
                    print(f"Link Text: {link_text}  {link_url}")
    return links



def get_domainspecificdetails(soup,domain):

    negative_domains = ["facebook.com"]
    for exclud in negative_domains:
        if exclud in domain:
            return {'sitename':''}
        
    sitename = ''
    text =  ''
    metades = soup.find("meta",  {"name":"description"})
    ogtitle = soup.find("meta",  {"property":"og:title"})
    title = soup.find("title")
    

    if title:
        text = title.text
    elif metades:
        text = text+ metades['content']
    elif ogtitle:
        text = text+ ogtitle['content']
    sitename = detectorgname(text)
    print({'sitename':sitename})
    return {'sitename':sitename}


def processlink(link,domainspecificdetails,domain,all_emails,all_numbers,additional_links,links):
    try:
        numbers_fromlink = []
        emails_fromlink = []
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36','Referer':link}
        response = requests.get(link,headers=headers,timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            mobiles, emails,note,name = extract_contact_info(soup, link)
            if domainspecificdetails == {}:
                domainspecificdetails = get_domainspecificdetails(soup,domain)

            for mobile in mobiles:
                if mobile not in all_numbers:
                    all_numbers.append(mobile) 
                    numbers_fromlink.append(mobile) 

            for email in emails:
                if email not in all_emails:
                    all_emails.append(email) 
                    emails_fromlink.append(email) 
            if len(additional_links) == 0 and len(links)<10 :
                additional_links.extend(get_recursive_links(soup,domain))
            return {'status':True,'data':[link,emails_fromlink,numbers_fromlink,note, domainspecificdetails,name,additional_links]}
        else:
            print(f"Failed to fetch HTML for {link}. Status Code: {response.status_code}")
            return {'status':False,'data':[]}
    except Exception as e:
        print(f"Failed to fetch HTML for {link}. error {e}")
        return {'status':False,'data':[]}



def fetch_contact_details(donain_data,cache,maxcontactfromdomain):
    ''' it will return list of object where one link will be one lead'''

    startTime = time.time()

    returning_list = []
    domain = donain_data['domain']

    if domain in cache:
        # print('return result from cache')
        return cache[domain]

    print('scraping domain', domain)

    links = donain_data['links']
    query = donain_data['row'][4]
    additional_links = [] # we will fill it by recursive links
    processedLinks = []
    
    
    domainspecificdetails = {}
    all_emails = []
    all_numbers = []
    for link in links:
        if link in processedLinks:
            continue
        if len(returning_list) >= maxcontactfromdomain:
            continue
        data = processlink(link,domainspecificdetails,domain,all_emails,all_numbers,additional_links,links)
        if data['status']:
            link,emails_fromlink,numbers_fromlink,note, domainspecificdetails,names,additional_links = data['data']
            print(link,emails_fromlink,numbers_fromlink,note, domainspecificdetails,names,additional_links)
            for email in emails_fromlink:
                returning_list.append({"domain":domain,"source":link,'email':email,
                                       "mobile":'',
                                       "query":query,"notes":note,
                                       "name":email.split('@')[0],
                                       "sitename":domainspecificdetails['sitename']
                                       ,'status':True})
            for i, number in enumerate(numbers_fromlink):
                returning_list.append({"domain":domain,"source":link,'email':"",
                                       "mobile":number,
                                       "query":query,"notes":note,
                                       "name":names[i] if i<len(names) else domainspecificdetails['sitename'],
                                       "sitename":domainspecificdetails['sitename']
                                       ,'status':True})
    for link in additional_links:
        if link in processedLinks:
            continue
        if len(returning_list) >= maxcontactfromdomain:
            continue
        data = processlink(link,domainspecificdetails,domain,all_emails,all_numbers,additional_links,links)
        if data['status']:
            link,emails_fromlink,numbers_fromlink,note, domainspecificdetails,names,additional_links = data['data']
            print(link,emails_fromlink,numbers_fromlink,note, domainspecificdetails,names,additional_links)
            for email in emails_fromlink:
                returning_list.append({"domain":domain,"source":link,'email':email,
                                       "mobile":'',
                                       "query":query,"notes":note,
                                       "name":email.split('@')[0],
                                       "sitename":domainspecificdetails['sitename']
                                       ,'status':True})
            for i, number in enumerate(numbers_fromlink):
                returning_list.append({"domain":domain,"source":link,'email':"",
                                       "mobile":number,
                                       "query":query,"notes":note,
                                       "name":names[i] if i<len(names) else domainspecificdetails['sitename'],
                                       "sitename":domainspecificdetails['sitename']
                                       ,'status':True})
    print('returning_list',returning_list)

    if len(returning_list)==0:
        returning_list.append({"domain":domain,'status':False})
    return returning_list

def get_domain(link):
    return urlparse(link).netloc

def list_domain(file_path):
    domains = {}

    df = pd.read_csv(file_path)
    
    for row in df.values.tolist():
        link = row[3]
        domain = get_domain(link)

        if domain in domains.keys():
            domains[domain]['links'].append(link)
        else:
            domains[domain] = {'links':[link], 'data':row}


    domainList = []
    for domain, value in domains.items():
        domainList.append({'domain':domain, 'links':value['links'],'row': value['data']})
    return domainList

def scrap_contacts(file_path,maxcontactfromdomain):
    ''' 
    This will read contact_processing/contactsheet.csv file and get all contact details
    Using threading
    '''

    # read cache for contacts
    try:
        with open('domain_cache.json', "r") as file:
            cache = json.load(file)
    except FileNotFoundError:
        cache = {}


    # list domain will read input file and get list of domains
    domainList = list_domain(file_path)
    num_threads = 200

    # add header in output file
    output_file_path = file_path.replace(f'{FINAL_OUTPUT_PATH}/', f'{contact_csv}/')  #google_out_filtered/CA_results.csv
    with open(output_file_path, 'w', newline='') as contact_details_csv_file:
        csv_writer = csv.writer(contact_details_csv_file)
        csv_writer.writerow(['domain','mobile_numbers', 'emails','source','name','sitename','query','notes'])




    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for donain_data in domainList:  #remove this one
            futures.append(executor.submit(fetch_contact_details, donain_data,cache,maxcontactfromdomain))
        all_domain_data = [future.result() for future in concurrent.futures.as_completed(futures)]




    # scrap data from a domain
    for domain_data in all_domain_data:
        try:
            if len(domain_data) !=0:
                cache[domain_data[0]['domain']] = domain_data

            with open(output_file_path, 'a', newline='',encoding='utf-8') as contact_details_csv_file:
                csv_writer = csv.writer(contact_details_csv_file)
                for linkdata in domain_data:
                    tostore = True
                    if 'status' in linkdata:
                        tostore = linkdata['status']

                    if tostore:
                        csv_writer.writerow([linkdata['domain'],linkdata['mobile'],
                                            linkdata['email'],linkdata['source'],
                                            linkdata['name'],linkdata['sitename'],
                                            linkdata['query'],linkdata['notes'],
                                            ])
        except Exception as e:
            print(f'error while storing result to contact out file',domain_data, e)
            continue

    with open('domain_cache.json', "w") as file:
        json.dump(cache, file)

    # Update output file to drive and update sheet
    drive_link = get_drive_link(output_file_path)
    return drive_link,output_file_path


    

def process_csv_files(query,urlsfiles,maxcontactfromdomain=10):
    return_data = {}
    contact_csvs = []
    for file_path in urlsfiles:
        state = file_path.replace(f'{FINAL_OUTPUT_PATH}/','').replace(FINAL_OUTPUT_PATH,'_results.csv')
        drive_link,output_file_path = scrap_contacts(file_path,maxcontactfromdomain)
        print(file_path,drive_link,output_file_path)
        return_data[state] = {'drive':drive_link,'csv_file':output_file_path}
        contact_csvs.append(output_file_path)
    return return_data, contact_csvs
    