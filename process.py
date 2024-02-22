import argparse
import json
import sys
import os
import requests
from helper.helper import store_output
from helper import step1 as S1
from helper import step2 as S2
from helper import step3 as S3

with open('prameters.json', 'r') as json_file:
    data = json.load(json_file)

query = data['query']
citystate = data.get('citystate',{})
negativekeywords = data.get('negativekeywords',[])
negativesites = data.get('negativesites',[]) 
maxgoogleresults = data.get('maxgoogleresults',20) 
maxcontactfromdomain = data.get('maxcontactfromdomain',10)
outputlocation = data.get('outputlocation',['csv','zoho','doc'])

print(query,citystate,negativekeywords,negativesites,maxgoogleresults,maxcontactfromdomain,outputlocation)


step1_result = S1.scrap_by_states(query, citystate,negativekeywords ,negativesites ,maxgoogleresults ,maxcontactfromdomain ,outputlocation)
if 'data' in step1_result:
    S1files = step1_result['data']['step1files']
    step1_result['data'] = {}
store_output(step1_result)


step2_result,contact_csvs = S2.process_csv_files(query, S1files,maxcontactfromdomain=maxcontactfromdomain)
store_output({'status':True, "message":'Step 2 completed', "data":step2_result})


if 'zoho' in outputlocation:
    print('upload to zoho')
    step3_status = S3.upload_to_zoho(contact_csvs)
    if step3_status:
        store_output({'status':True, "message":'Step 3 completed', "data":step2_result})

store_output({"COMPLETED":"COMPLETED"})
