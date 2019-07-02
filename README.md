# TeslaDR
Tesla Demand Response based on CAISO market prices

This project will monitor CAISO prices at http://oasis.caiso.com/oasisapi/prc_hub_lmp/PRC_HUB_LMP.html every 5 minutes. When prices are over $100/MWh at NP15, a signal will be sent to all registered tesla accounts to shut off charging until prices drop below $100/MWh.

Done so far:
  -Initial functions defined to read vehicle state and send basic commands. Located in tesla.py
  -SQL database built to store users, login info, and basic vehicle info. Create database using setup.py
  -flask website built as front end to access database. features include:
    -register to create account, including email verification
    -login (need to add failed login monitoring and lockout)
    -Account management page with:
      -update password (need to add email notification when updated)
      -change email, including verification (need to add notification to old email address)
      -Account deletion
    -Link tesla account (need to add failed login monitoring/lockout, and unlink)
    -Homepage with list of vehicles and link to each
    -Vehicle details page with climate state, charge state, and location
      -Functions to start and stop charging
      -Ability to set managed charging aggressiveness (1-100 scale stored in database)
  
To do:
  -Back end database cron jobs:
    -refresh tokens daily (for tokens expiring in the next three days)
    -Regularly poll vehicles for sleep state, charge state, and location
      -Calculate relevant benchmark price from location (euclidian distance)
    -Monitor CAISO price
      -trigger update of vehicle info when CAISO price hits threshold
      -pause charging if conditions met
      -log DR events
  -Front end:
    -Add account management:
      -Add unlink tesla account
    -Security notifications:
      -Password change
      -email change (to old email)
    -Failed login monitoring and locking
      -main account
      -tesla account

Long-term enhancements include:
  -Track Demand Response (DR) events and prices to calculate wholesale value of energy not used
  -Place DR event location within electric utility service area
  -Allow user to set up data logging
  -Allow users to set custom price threshold
  -Alow users to set maximum number of DR responses to skip in any 24-hour period
