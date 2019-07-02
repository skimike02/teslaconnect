import smtplib
import ssl
import requests

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer

import config

def Degrees(temp, is_far):
    if is_far==False:
        r=str(temp)+'°C'
    else:
        r=str(int(temp*9.0/5+32))+'°F'
    return r

def html_table(query,headers=True):
    r='<table>'
    if headers==True:
        r+='  <tr><th>'
        r+='    </th><th>'.join(query[0])
        r+='  </th></tr>'
        query=query[1:len(query)]
    for sublist in query:
        r+='  <tr><td>'
        r+='    </td><td>'.join(sublist)
        r+='  </td></tr>'
    r+='</table>'
    return r

def SendEmailMailgun(recipient,subject,messagetext,messagehtml):
    return requests.post(
        f'''https://api.mailgun.net/v3/mail.{config.mailgun_domain}/messages''',
        auth=("api", config.mailgun_API),
        data={"from": config.mailgun_from,
              "to": recipient,
              "subject": subject,
              "text": messagetext,
              "html": messagehtml},
        verify=config.ssl_validation)

def SendEmailSMTP(recipient,subject,messagetext,messagehtml):
    sender = config.emailsender
    password = config.emailpassword
    smtp_server = config.smtp_server
    port = config.smtpport

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(MIMEText(messagetext, "plain"))
    message.attach(MIMEText(messagehtml, "html"))

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender, password)
        server.sendmail(
            sender, recipient, message.as_string()
        )
        
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(config.static_key)
    return serializer.dumps(email, salt=config.staticsalt)

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(config.static_key)
    try:
        email = serializer.loads(
            token,
            salt=config.staticsalt,
            max_age=expiration
        )
    except:
        return False
    return email