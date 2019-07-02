import requests
import json
import time
from lxml import html

def Authenticate(email,password):
    url="https://owner-api.teslamotors.com/oauth/token"
    client_id="e4a9949fcfa04068f59abb5a658f2bac0a3428e4652315490b659d5ab3f35a9e"
    client_secret="c75f14bbadc8bee3a7594412c31416f8300256d7668ea7e6e7f06727bfb9d220"
    payload = {"grant_type": "password","client_id": client_id,"client_secret": client_secret,"email": email,"password": password}
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    a=json.loads(r.content.decode('utf-8'))
    #returns access token, token type, expires_in, refresh_token, and created_at
    if 'access_token' in a:
        return a
    else:
        return 'Tesla credentials invalid'

def RefreshToken(refresh_token):
    url="https://owner-api.teslamotors.com/oauth/token"
    client_id="e4a9949fcfa04068f59abb5a658f2bac0a3428e4652315490b659d5ab3f35a9e"
    client_secret="c75f14bbadc8bee3a7594412c31416f8300256d7668ea7e6e7f06727bfb9d220"
    payload = {"grant_type": "refresh_token","client_id": client_id,"client_secret": client_secret,"refresh_token": refresh_token}
    headers = {"Content-Type": "application/json"}
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    a=json.loads(r.content.decode('utf-8'))
    #returns access token, token type, expires_in, refresh_token, and created_at
    if 'access_token' in a:
        return a
    else:
        return 'Tesla credentials invalid'
    
def GetIDs(access_token):
    url="https://owner-api.teslamotors.com/api/1/vehicles"
    headers = {"Authorization": "Bearer "+access_token}
    payload={}
    r = requests.get(url, data=json.dumps(payload), headers=headers)
    if r.status_code!=200:
        a="Error: http response "+str(r.status_code)+" "+r.reason
        return a
    else:
        a=json.loads(r.content.decode('utf-8'))
        response=a['response']
        return response
 
def Wake(access_token,ID,delay):
    url="https://owner-api.teslamotors.com/api/1/vehicles/"+ID+"/wake_up"
    headers = {"Authorization": "Bearer "+access_token}
    payload={}
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    if r.status_code!=200:
        a="Error: http response "+str(r.status_code)+" "+r.reason
    else:
        a=json.loads(r.content.decode('utf-8'))
        time.sleep(delay)
    return a

def GetDataNoWake(access_token,ID,endpoint):
    url="https://owner-api.teslamotors.com/api/1/vehicles/"+ID+"/"+endpoint
    headers = {"Authorization": "Bearer "+access_token}
    payload={}
    r = requests.get(url, data=json.dumps(payload), headers=headers, timeout=10)
    a=json.loads(r.content.decode('utf-8'))
    return a

def GetData(access_token,ID,endpoint):
    attempt=1
    a=GetDataNoWake(access_token,ID,endpoint)
    while attempt<5 and a['response'] is None:
        Wake(access_token,ID,3)
        a=GetDataNoWake(access_token,ID,endpoint)
        attempt+=1
    if a['response'] is None:
        return "Error: Unable to wake vehicle"
    else:
        return a    

def AllData(access_token,ID):
    endpoint="data"
    a=GetData(access_token,ID,endpoint)
    return a

def VehicleState(access_token,ID):
    endpoint="data_request/vehicle_state"
    a=GetData(access_token,ID,endpoint)
    return a

def ChargeState(access_token,ID):
    endpoint="data_request/charge_state"
    a=GetData(access_token,ID,endpoint)
    return a

def ClimateState(access_token,ID):
    endpoint="data_request/climate_state"
    a=GetData(access_token,ID,endpoint)
    return a

def DriveState(access_token,ID):
    endpoint="data_request/drive_state"
    a=GetData(access_token,ID,endpoint)
    return a

def ChargingSites(access_token,ID):
    endpoint="nearby_charging_sites"
    a=GetData(access_token,ID,endpoint)
    return a

def ChargerState(access_token,ID):
    #Get list of supercharger names and links. Amenities and charge rate only stored on web. Not availabe via API.
    headers={'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
    Superchargerlist="https://www.tesla.com/findus/list/superchargers/United+States"
    r=requests.get(Superchargerlist,headers=headers)
    tree=html.fromstring(r.content)
    links=tree.xpath('//address/a/@href')
    names=tree.xpath('//address/a/text()')
    #Get nearest charger name and available stalls from API
    chargerdetails=ChargingSites(access_token,ID)['response']['superchargers'][0]
    available_stalls=chargerdetails['available_stalls']
    name=chargerdetails['name']+" Supercharger"
    #Convert name to link and fetch amenities
    link=links[names.index(name)]
    url="https://www.tesla.com"+link
    r=requests.get(url,headers=headers)
    tree=html.fromstring(r.content)
    charging=tree.xpath('''//address[@class='vcard']/../p[2]/text()''')
    restrooms=tree.xpath('''//address[@class='vcard']/../p[3]/text()''')
    restaurants=tree.xpath('''//address[@class='vcard']/../p[4]/text()''')
    shopping=tree.xpath('''//address[@class='vcard']/../p[5]/text()''')
    #Build response data
    response={"available _stalls":available_stalls,"charging":charging, "restrooms":restrooms, "restaurants":restaurants, "shopping":shopping}
    return response

def SendCommand(access_token,ID,endpoint):
    url="https://owner-api.teslamotors.com/api/1/vehicles/"+ID+"/"+endpoint
    headers = {"Authorization": "Bearer "+access_token}
    payload={}
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    if r.status_code!=200:
        a="Error: http response "+str(r.status_code)+" "+r.reason
    else:
        a=json.loads(r.content.decode('utf-8'))
    return a

def StopCharge(access_token,ID):
    endpoint="charge_stop"
    a=SendCommand(access_token,ID,endpoint)
    return a

def StartCharge(access_token,ID):
    endpoint="charge_start"
    a=SendCommand(access_token,ID,endpoint)
    return a

def PauseCharge(access_token,ID,maxintervals):
    Wake(access_token,ID)
    chargestate=ChargeState(access_token,ID)
    #Read current charge state
    #if charging
        #Send stop
        #Write to DB ID,charge_rate, scheduled_charging_start_time, time_to_full_charge
        #Store charge rate and start time
        #Calculate time charge would have ended w/o intervention now+((charge limit-current charge)/charge rate)
    #if scheduled to charge
        #write scheduled charge time to DB
        #turn off scheduled charge
    #else (also assume no respone/vehicle sleeping=not charging)
