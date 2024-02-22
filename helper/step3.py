import requests
import json
import os
import pandas as pd

def get_access_token():
    url = 'https://accounts.zoho.com/oauth/v2/token'
    # payload = {'grant_type': 'authorization_code',
    #             'client_id': '1000.58ZC52A8NB3R0LYIX9J1AHYNJJFGAT',
    #             'client_secret': 'ad1db765f3e0023ec638ea7451b4553ab2c0897358',
    #             'code': '1000.713961569273d7c522dc0de931e88af6.524c236c2225e51032fbe4eed7d01e68'}

    payload = {'grant_type': 'refresh_token',
                'client_id': '1000.K712EJPH1MEI0EGSNOX46V4BK11VVU',
                'client_secret': '054aabc9b126a11eaed9b0e7a707ab776da190af0c',
                'refresh_token': '1000.04c7c1a7f5d4bd4fac73d37f15ee6179.403e5c5844d2bcaa979bcc7a7a44e5b6'}

    response = requests.request("POST", url, data=payload)

    return response.json()['access_token']

def upload_to_server(data, acesstocken):
    url = "https://www.zohoapis.com/crm/v2/Leads"

    # payload = json.dumps({
    # "data": [
    #     {
    #     "Email": "test@noemail.com",
    #     "Mailing_State": "MD",
    #     "Description": "this is test",
    #     "Title": "Quality Engineer",
    #     "Mobile": "555-555-5555",
    #     "Last_Name": "test",
    #     "Lead_Source": "Web Download"
    #     },
    #     {
    #     "Email": "test@noemail.com",
    #     "Mailing_State": "MD",
    #     "Description": "this is test",
    #     "Title": "Quality Engineer",
    #     "Mobile": "555-555-5555",
    #     "Last_Name": "test",
    #     "Lead_Source": "Web Download"
    #     }
    # ]
    # })
    payload = json.dumps({
        "data":data
    })


    headers = {
    'Authorization': f'Zoho-oauthtoken {acesstocken}',
    'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.json())



def upload_to_zoho(contact_csvs):
    try:

        access_token = get_access_token()
        print(access_token)

        types = ["Youth League","High School","Amateur","Surgeon","Pre School","Booster","Realtor",
            "Association","HS League","Real Estate","Finance","Youth","Home Improvement","Medical","Consumer",
            "Broker","Sales & Marketing","Manufacturer","Sponsor"]
        sports = ["Football","Basketball","Baseball","Softball","Track & Field","Soccer","Wrestling 2","Performing Arts"]




        zoho_dump_data =  []
        count = 0



        for out_csv in contact_csvs:
            


            df = pd.read_csv(out_csv)
            count1500 = 1
            for index,row in df.iterrows():
                print(row)
                mobile_number = row['mobile_numbers']
                email = row['emails']
                query = row['query']
                domain = row['domain']
                sitename = row['sitename']
                name = row['name']
                source = row['source']
                list_str = ' '.join(query.split(' ')[2:])
                data = {
                "Company": sitename,
                "Website": domain,
                "Last_Name": name,
                "Lead_Source": "Web Research",
                "Python_List_Name": f'{list_str} {count//1500 +1}',
                "City": query.split(' ')[0],
                "State": query.split(' ')[1],
                "Country": "United States",
                }

                if type(mobile_number)==str:
                    data["Mobile"] = mobile_number

                if type(email)==str:
                    data["Email"] = email

                for typee in types:
                    if typee.lower() in query.lower():
                        data["Type"] = typee
                        break

                for sport in sports:
                    print(sport.lower() in query.lower())
                    print(sport, query)
                    if sport.lower() in query.lower():
                        data["Sport"] = sport
                        # data["Sport_Activity1"] = sport
                        
                        break



                zoho_dump_data.append(data)

                count=count+1
                if count>=100:
                    print(zoho_dump_data)
                    upload_to_server(zoho_dump_data,access_token)
                    count = 0
                    zoho_dump_data = []
                    # break


            upload_to_server(zoho_dump_data,access_token)
        return True
    except Exception as e:
        print('Error while uploading leads to zoho',e)
        return False


