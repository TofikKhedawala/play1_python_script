import csv
import requests
import json
import os
import time
import pandas as pd
import concurrent.futures
import time
from .config import *

try:
    with open(cacheFile, "r") as file:
        cache = json.load(file)
except FileNotFoundError:
    cache = {}



def googleSerchAPI(query, sleep_interval=1, num_results=10):

    returnList = []
    add_cache = {}
    for start in range(1, num_results, 10):
        payload = {'key':API_KEY,'cx':cx,'gl':'US','q':query,"start":start}

        print(query, start)
        if f'{query},{start}' in cache:
            print(f'{query},{start} is in cache returining from cache')
            datas = cache[f'{query},{start}']
            returnList.extend(datas)
            continue

        # print(payload)
        responce = requests.get('https://customsearch.googleapis.com/customsearch/v1', params=payload)
        print('sleep for ',sleep_interval )
        time.sleep(sleep_interval)
        if responce.status_code != 200:
            print('error while google', responce)
            break
        else:
            try:
                datas = [j['link'] for j in responce.json()["items"]]
                add_cache[f'{query},{start}'] = datas
                # time.sleep(sleep_interval)
            except Exception as e:
                print(responce.json())
                print(e)
                break
            returnList.extend(datas)
    # write to chache to use next time
    # with open(cacheFile, "w") as file:
    #     json.dump(cache, file)
    
    return returnList,add_cache


def scrap_by_city(query, city,state,num_results=20):
    query = query.replace('city state', f'{city} {state}')
    # query = query.replace('city', city).replace('state', state)
    search_result_city,add_cache = googleSerchAPI(query, sleep_interval=3, num_results=num_results)
    if len(search_result_city)==0:
        return {'status':False}

    if 'baseball' in query:
        sport = 'baseball'
    elif 'softball' in query:
        sport = 'softball'
    elif 'football' in query:
        sport = 'football'
    else:
        sport = 'None'

    return {'status':True, 'links':search_result_city,'query':query, "city":city,"state":state,'sport':sport,'add_cache':add_cache }

def checkLinkExclude(x,negativesites):
    for exclud in negativesites:
        if exclud in x:
            return True
    return False

def store_state_result(state, state_results,query,negativesites):
    '''
    its work in three step
    1. create csv file
    2. read and filter results
    '''


    # step 1 create csv file
    file_path = os.path.join(f"{GOOGLE_OUT_Path}", f"{state}.csv")

    print("file_path****",file_path)

    with open(file_path, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        for city_result in state_results:
            for link in city_result['links']:
                csv_writer.writerow([state, city_result['city'], city_result['sport'], link,city_result['query'] ])

    # step 2. read and filter results
    df = pd.read_csv(file_path, names=["state", "city", "sport", "link", 'keyword'])
    print("df***",df)
    df['excluded'] = False
    df['linkInExclude'] = False
    df['excludedReason'] = ''
    df['duplicate'] = df.duplicated(['link'], keep='first')
    df.loc[df["duplicate"] == True, "excluded"] = True
    df.loc[df["duplicate"] == True, "excludedReason"] = 'Duplicate link'
    print("df**after**",df)

    df['linkInExclude'] = df['link'].apply(lambda x: checkLinkExclude(x,negativesites))
    df.loc[df["linkInExclude"] == True, "excludedReason"] = 'Excluded link'
    df.loc[df["linkInExclude"] == True, "excluded"] = True
    df = df[df['excluded'] == False]
    df.drop(columns=['linkInExclude', 'excludedReason', 'duplicate', 'excluded'], inplace=True)

    # Update the output file name based on the state
    output_file_name = f'{FINAL_OUTPUT_PATH}/{state}_results.csv'
    df.to_csv(output_file_name, index=False)
    print("**output_file_name**",output_file_name)
    return output_file_name




def scrap_by_states(query, city_state_formated,negativekeywords ,negativesites ,maxgoogleresults ,maxcontactfromdomain ,outputlocation):
    query_status = {"status":True, "message":'Step 1 completed',"data":{}}
    created_files = []
    try:
        
        for state in city_state_formated.keys():
            print('run for',query, state)
            all_citys = list(set(city_state_formated[state]))


            # loop over all citys with threading
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKER) as executor:
                futures = []
                for city in all_citys:
                    futures.append(executor.submit(scrap_by_city, query, city,state,num_results=maxgoogleresults))
                all_citys_scrap_results = [future.result() for future in concurrent.futures.as_completed(futures)]
            



            # updating cache
            for scrap_result in all_citys_scrap_results:
                if scrap_result['status']:
                    for key,value in scrap_result['add_cache'].items():
                        cache[key] = value
                    with open(cacheFile, "w") as file:
                        json.dump(cache, file)
                    print(scrap_result['query'], 'is added in cache')
                else:
                    continue



            # check is all city processed sucsessfully
            all_citys_processed = True
            for scrap_result in all_citys_scrap_results:
                if scrap_result['status']:
                    print(scrap_result['query'], 'is fine')
                else:
                    all_citys_processed = False
                    break
            
            # update results to drive
            if all_citys_processed:
                fileName = store_state_result(state,all_citys_scrap_results,query,negativesites)
                created_files.append(fileName)
                print("created_files*******",created_files)
                query_status['data']['step1files'] = created_files
            else:
                print('Got error while scraping results for', state)
                query_status = {"status":False, "message":f'Got error while scraping results for {state}'}
                break
    except Exception as e:
        return {"status":False, "message":'Fail to get data from google'}


    return query_status
