import users

sql='''CREATE TABLE users (username text NOT NULL, email text NOT NULL, createtimestamp int NOT NULL, subscription text NOT NULL, nacl text NOT NULL, hash text NOT NULL, confirmed integer NOT NULL, confirmedtimestamp int, pendingemail text, emailreqtimestamp int);'''
users.ExecSQL(sql)
sql='''CREATE TABLE tokens (username text NOT NULL, email text NOT NULL, access_token text NOT NULL, refresh_token text NOT NULL, expiry int NOT NULL);'''
users.ExecSQL(sql)
sql='''CREATE TABLE vehicles (username text NOT NULL, email text NOT NULL, display_name text NOT NULL, vin text NOT NULL, id text NOT NULL, state text NOT NULL, createtimestamp int NOT NULL);'''
users.ExecSQL(sql)
sql='''CREATE TABLE managedcharging (id text NOT NULL, threshold int NOT NULL, tripend date);'''
users.ExecSQL(sql)

