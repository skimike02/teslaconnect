# -*- coding: utf-8 -*-

import requests
import time
import random
from bs4 import BeautifulSoup as bs

interval=1
jitter=1

prior_version=""

while True:
    url="https://teslafi.com/firmware/"
    r=requests.get(url)
    soup=bs(r.content, features="lxml")
    table=soup.table
    current_version=table.td.text
    if current_version!=prior_version:
        print("version changed")
        prior_version=current_version
    else:
        print("version same")
    time.sleep(interval*60+random.random()*jitter*60-jitter/2*60)
