import sqlite3
import time
import random
import string
import scrypt

import tesla
import config

static_key=config.static_key
staticsalt=config.staticsalt
db_file=config.db_file

'''
To do:
    add functions:
        DropUser(username, password)
        ChangeEmail(username)
        reset password(username)
    edit functions:
        require email confirmation to create account
        log failed login attempts
        lock account after n number of failed logins in last 24 hours
'''

def ExecSQL(sql):
    try:
        conn=sqlite3.connect(db_file)
        cur=conn.cursor()
        cur.execute(sql)
        conn.commit()
        return cur.fetchall()
        conn.close()
    except BaseException as error:
        return error

def CreateUser(username,email,subscription,password,password2):
    if password!=password2:
        return 'Your password and confirmation password do not match'
    else:
        username=username.lower()
        dynamicsalt=''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(15))
        now=str(time.time()).replace('.', '')
        #check for user/email in database. If exists, return error
        existingusers=ExecSQL(f'''Select count(*) from users where username='{username}' or email='{email}';''')[0][0]
        if existingusers>0:
            return 'That user name or e-mail is already in use'
        else:
            #hash function to create hash
            prehash=username+password+now+dynamicsalt
            hash=scrypt.hash(prehash,staticsalt).hex()
            sql='''INSERT INTO users (username, email, createtimestamp, subscription, nacl, hash, confirmed) VALUES'''
            sql+=f'''('{username}','{email}','{now}','{subscription}','{dynamicsalt}','{hash}',0);'''
            ExecSQL(sql)
            success=ExecSQL(f'''Select count(*) from users where username='{username}' or email='{email}';''')[0][0]==1
            if success is True:
                return 'Account successfully created'
            else:
                return 'The server was unable to process your request'
               
def ConfirmUser(email):
    now=str(time.time()).replace('.', '')
    sql=f'''UPDATE users SET confirmed='1', confirmedtimestamp='{now}' WHERE email='{email}';'''
    ExecSQL(sql)

def ValidateUser(username,password):
    username=username.lower()
    record=ExecSQL(f'''select createtimestamp, nacl, hash from users where username='{username}';''')
    if len(record)>1:
        return {'login':'Multiple users','confirmed':False}
    elif len(record)==0:
        return {'login':'User not found','confirmed':False}
    else:
        now=str(record[0][0])
        dynamicsalt=str(record[0][1])
        targethash=str(record[0][2])
        prehash=username+password+now+dynamicsalt
        hash=scrypt.hash(prehash,staticsalt).hex()
        if hash==targethash:
            confirmed=ExecSQL(f'''SELECT confirmed FROM users WHERE username='{username}';''')[0][0]
            return {'login':'Validated', 'confirmed':confirmed==1}
        else:
            return {'login':'Invalid credentials', 'confirmed':False}

def UpdatePassword(username,oldpassword,newpassword,newpassword2):
    username=username.lower()
    validation=ValidateUser(username,oldpassword)
    if validation['login']!='Validated':
        return 'Invalid credentials'
    elif newpassword!=newpassword2:
        return 'Your password and confirmation password do not match'
    else:
        staticsalt='589MJ0P5IV'
        record=ExecSQL(f'''select createtimestamp, nacl, hash from users where username='{username}';''')
        if len(record)>1:
            return 'Error2'
        elif len(record)==0:
            return 'Invalid credentials'
        else:
            now=str(record[0][0])
            dynamicsalt=str(record[0][1])
            prehash=username+newpassword+now+dynamicsalt
            hash=scrypt.hash(prehash,staticsalt).hex()
            sql=f'''UPDATE users set nacl='{dynamicsalt}', hash='{hash}' WHERE username = '{username}';'''
            ExecSQL(sql)
            success=ExecSQL(f'''Select hash from users where username='{username}';''')[0][0]==hash
            if success is True:
                return 'Account successfully updated'
            else:
                return 'The server was unable to process your request'     

def encrypt(username,payload,action):
    username=username.lower()
    sql = f'''SELECT createtimestamp, nacl from users where username = '{username}';'''
    record=ExecSQL(sql)
    if len(record)>1:
        return 'Error2'
    elif len(record)==0:
        return 'User not found'
    else:
        now=str(record[0][0])
        dynamicsalt=str(record[0][1])
        password=username+now+static_key+dynamicsalt
        if action=='encrypt':
            response=scrypt.encrypt(payload,password,maxtime=.5).hex()
        elif action=='decrypt':
            response=scrypt.decrypt(bytes.fromhex(payload),password)
        else:
            return 'Error, unknown action'
        return response
    
def LinkAccounts(username,email,password):
    username=username.lower()
    a=tesla.Authenticate(email,password)
    if a == 'Tesla credentials invalid':
        return a
    else:
        access_token=encrypt(username,a['access_token'],'encrypt')
        refresh_token=encrypt(username,a['refresh_token'],'encrypt')
        expiry=a['created_at']+a['expires_in']
        #write encrypted tokens to DB
        sql=f'''DELETE FROM tokens WHERE username='{username}' and email='{email}';'''
        ExecSQL(sql)
        sql='''INSERT INTO tokens (username,email,access_token,refresh_token,expiry) VALUES'''
        sql+=f'''('{username}','{email}','{access_token}','{refresh_token}','{expiry}');'''
        ExecSQL(sql)
        #get current vehicles
        a=GetVehicles(username,email)        
        if a=='Vehicles loaded':
            return 'Account linked and vehicles loaded'
        else:
            return 'Account linked. Error retrieving vehicles.'

def GetToken(username,email):
    username=username.lower()
    sql=f'''SELECT access_token from tokens WHERE username='{username}' and email='{email}';'''
    record=ExecSQL(sql)
    if len(record)>1:
        return 'Error2'
    elif len(record)==0:
        return 'User not found'
    else:
        access_token=encrypt(username,record[0][0],'decrypt')
        return access_token

def GetVehicles(username,email):
    username=username.lower()
    access_token=GetToken(username,email)
    vehicles=tesla.GetIDs(access_token)
    if vehicles=='Error: http response 401 Unauthorized':
        return vehicles
    else:
        sql=f'''DELETE FROM vehicles WHERE username='{username}' AND email='{email}';'''
        ExecSQL(sql)
        for vehicle in vehicles:
            display_name=vehicle['display_name']
            vin=vehicle['vin']
            id=str(vehicle['id_s'])
            state=vehicle['state']
            createtimestamp=int(time.time())
            sql='''INSERT INTO vehicles (username, email, display_name, vin, id, state, createtimestamp) VALUES'''
            sql+=f'''('{username}', '{email}', '{display_name}', '{vin}', '{id}', '{state}', '{createtimestamp}');'''
            ExecSQL(sql)
        return 'Vehicles loaded'

def RetrieveVehicles(username):
    username=username.lower()
    sql=f'''SELECT email, display_name, vin, state, id FROM vehicles WHERE username='{username}';'''
    results=ExecSQL(sql)
    if len(results)==0:
        return 'No vehicles identified'
    else:
        table=[]
        for result in results:
            result=list(result)
            result[1]=f'''<a href="/vehicles?id={result[4]}"> {result[1]}<a>'''
            del result[4]
            table.append(tuple(result))
        r=[('Tesla email','Vehicle Name','VIN','Last Reported State')]
        r+=table
        return r
    
def VehicleInfo(username,id):
    username=username.lower()
    #check that user/id relationhip is valid
    record=ExecSQL(f'''SELECT email FROM vehicles WHERE id='{id}' AND username='{username}';''')[0]
    email=record[0]
    access_token=GetToken(username,email)
    return tesla.AllData(access_token,id)['response']
    
def SendCommand(username,id,command):
    username=username.lower()
    #check that user/id relationhip is valid
    record=ExecSQL(f'''SELECT email FROM vehicles WHERE id='{id}' AND username='{username}';''')[0]
    email=record[0]
    access_token=GetToken(username,email)
    return tesla.SendCommand(access_token,id,command)['response']

def DeleteAccount(username,password):
    username=username.lower()
    if ValidateUser(username,password)=='Validated':
        sql=f'''DELETE FROM vehicles WHERE username='{username}';'''
        ExecSQL(sql)
        sql=f'''DELETE FROM tokens WHERE username='{username}';'''
        ExecSQL(sql)
        sql=f'''DELETE FROM users WHERE username='{username}';'''
        ExecSQL(sql)
        return 'Account Deleted'
    else:
        return 'Invalid Credentials'

def RefreshTokens(days: int):
    seconds=days*24*60*60
    target=int(time.time())+seconds
    sql=f'''SELECT username, refresh_token, expiry FROM tokens where expiry<'{target}';'''
    r=ExecSQL(sql)
    records_updated=0
    for token in r:
        username=token[0]
        refresh_token=token[1]
        unencrypted=encrypt(username,refresh_token,'decrypt')
        new_token=tesla.RefreshToken(unencrypted)
        if new_token=='Tesla credentials invalid':
            return new_token
        else:
            access_token=encrypt(token[0],new_token['access_token'],'encrypt')
            refresh_token=encrypt(token[0],new_token['refresh_token'],'encrypt')
            expiry=new_token['created_at']+new_token['expires_in']
            sql=f'''UPDATE tokens SET access_token='{access_token}', refresh_token='{refresh_token}', expiry='{expiry}' WHERE username='{username}';'''
            ExecSQL(sql)
            records_updated+=1
    return f'''Updated {records_updated} records'''

def UpdateThreshold(id, threshold):
    sql=f'''SELECT count(*) FROM managedcharging WHERE id='{id}';'''
    records=ExecSQL(sql)[0][0]
    if records==0:
        sql='''INSERT INTO managedcharging (id, threshold) VALUES'''
        sql+=f'''('{id}', '{threshold}');'''
    else:
        sql=f'''UPDATE managedcharging SET threshold='{threshold}' WHERE id='{id}';'''
    ExecSQL(sql)

def ValidIDforUser(username,id):
    username=username.lower()
    sql=f'''SELECT count(*) FROM vehicles WHERE username='{username}' AND id='{id}';'''
    return ExecSQL(sql)[0][0]==1
