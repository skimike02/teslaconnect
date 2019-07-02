#Set these values before launching setup.py. When complete, save the file as config.py


staticsalt='abc123'  #enter a random string. This will be used to salt passwords before hashing. This is in addition to a dynamic hash. If changed after launch, no old passwords will validate successfully.
static_key='123abc'  #enter a random string. This is used to encrypt and decrypt sensitive non-password data in the database.
google_api_key='Iamagoogleapikey' #Enter your googla maps api key. This is used for displaying embedded maps with the location of your vehicle.
db_file='/var/www/html/app/database/sql.db' #Enter the path from root to where your database will live.


#Set up service email account
#emailsender = "no-reply@domain.com"
#emailpassword = "verysecurepassword"
#smtp_server = "mail.domain.com"
#smtpport = "465"

#Set up mailgun account for sending email
mailgun_domain = "domain.com"
mailgun_API = "API key for the domain above"
mailgun_from = "from <name@domain.com>"

flask_debug = False
ssl_validation = True
