from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
import os
import time

import users
import misc
from decorators import check_confirmed, login_required
import config


google_api_key=config.google_api_key

app = Flask(__name__)
app.secret_key=os.urandom(12)

@app.route("/")
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return redirect(url_for('home'))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        validation=users.ValidateUser(request.form['username'],request.form['password'])
        if validation['login'] != 'Validated':
            error = 'Invalid credentials'
        else:
            session['logged_in'] = True
            session['username'] = request.form['username'].lower()
            if validation['confirmed']:
                return redirect(url_for('index'))
            else:
                return redirect(url_for('unconfirmed'))
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET','POST'])
def register():
    error = None
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        password2=request.form['password2']
        email=request.form['email']
        subscription='free'
        response=users.CreateUser(username,email,subscription,password,password2)
        if response!='Account successfully created':
            error=response
        else:
            token=misc.generate_confirmation_token(email)
            confirm_url=url_for('confirm_email', token=token, _external=True)
            subject="Please confirm your email address"
            messagetext=render_template('verification.txt', url=confirm_url)
            messagehtml=render_template('verification.html', url=confirm_url)
            misc.SendEmailMailgun(email,subject,messagetext,messagehtml)
            flash('A confirmation email has been sent via email.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = misc.confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        email = None
    if users.ExecSQL(f'''SELECT count(*) FROM users WHERE email='{email}';''')[0][0]==0:
        flash('The confirmation link is invalid or has expired.', 'danger')
    else:
        confirmed = users.ExecSQL(f'''SELECT confirmed FROM users WHERE email='{email}';''')[0][0]
        if confirmed==1:
            flash('Your account has already been confirmed. Please login.', 'success')
        else:
            users.ConfirmUser(email)
            flash('You have confirmed your account.', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session['logged_in'] = False
    flash('You have been logged out')
    return index()

@app.route('/unconfirmed')
@login_required
def unconfirmed():
    try:
        confirmed=users.ExecSQL('''SELECT confirmed FROM users WHERE username='{session['username']}';''')[0][0]
    except:
        confirmed=0
    if confirmed==1:
        return redirect('index')
    flash('Please confirm your account.', 'warning')
    return render_template('unconfirmed.html')  

@app.route('/resend')
@login_required
def resend():
    email=users.ExecSQL(f'''SELECT email FROM users WHERE username='{session['username']}';''')[0][0]
    token=misc.generate_confirmation_token(email)
    confirm_url=url_for('confirm_email', token=token, _external=True)
    subject="Please confirm your email address"
    messagetext=render_template('verification.txt', url=confirm_url)
    messagehtml=render_template('verification.html', url=confirm_url)
    misc.SendEmailMailgun(email,subject,messagetext,messagehtml)
    flash('A confirmation email has been sent via email.', 'success')
    return redirect(url_for('unconfirmed'))

@app.route('/account')
@login_required
@check_confirmed
def account():
    return render_template('account.html')  

@app.route('/link', methods=['GET','POST'])
@login_required
@check_confirmed
def link():    
    error = None
    if request.method == 'POST':
        a=users.LinkAccounts(session['username'],request.form['email'],request.form['password'])
        if a=='Account linked and vehicles loaded' or a=='Account linked. Error retrieving vehicles.':
            flash(a)
            return redirect(url_for('index'))
        else:
            error=a
    return render_template('link.html',error=error)

@app.route('/changepass', methods=['GET','POST'])
@login_required
@check_confirmed
def changepass():    
    error = None
    if request.method == 'POST':
        a=users.UpdatePassword(session['username'],request.form['oldpassword'],request.form['newpassword'],request.form['newpassword2'])
        if a=='Account successfully updated':
            flash(a)
            return redirect(url_for('index'))
        else:
            error=a
    return render_template('changepass.html',error=error)

@app.route('/change_email', methods=['GET','POST'])
@login_required
@check_confirmed
def change_email():    
    error = None
    if request.method == 'POST':
        if users.ExecSQL(f'''SELECT count(*) FROM users WHERE email='{request.form['newemail']}';''')[0][0]==0:
            now=str(time.time()).replace('.', '')
            users.ExecSQL(f'''UPDATE users SET pendingemail='{request.form['newemail']}',emailreqtimestamp='{now}' WHERE username='{session['username']}';''')
            #construct and send verification email
            token=misc.generate_confirmation_token(session['username'])
            confirm_url=url_for('confirm_new_email', token=token, _external=True)
            subject="Please confirm your email address"
            messagetext=render_template('verification.txt', url=confirm_url)
            messagehtml=render_template('verification.html', url=confirm_url)
            misc.SendEmailMailgun(request.form['newemail'],subject,messagetext,messagehtml)
            flash('verification email sent')
            return redirect(url_for('index'))
        else:
            error='The email address requested is already in use.'
    return render_template('change_email.html',error=error)

@app.route('/confirm_email/<token>')
def confirm_new_email(token):
    try:
        username = misc.confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired. Please try updating your email address again.', 'danger')
        return redirect(url_for('change_email'))
    if users.ExecSQL(f'''SELECT count(*) FROM users WHERE pendingemail<>'' AND username='{username}';''')[0][0]==0:
        flash('Your new email address has already been confirmed.', 'success')
        return redirect(url_for('index'))
    users.ExecSQL(f'''UPDATE users SET email=pendingemail, pendingemail='', emailreqtimestamp='' WHERE username='{username}';''')
    flash('Your new email address has been confirmed.', 'success')
    return redirect(url_for('index'))

@app.route('/delete', methods=['GET','POST'])
@login_required
@check_confirmed
def delete():    
    error = None
    if request.method == 'POST':
        a=users.DeleteAccount(session['username'],request.form['password'])
        if a=='Account Deleted':
            flash('Your account has been deleted', 'success')
            return redirect(url_for('index'))
        else:
            error=a
    return render_template('delete.html',error=error)

@app.route("/home")
@login_required
@check_confirmed
def home():
    vehicles=users.RetrieveVehicles(session['username'])
    if vehicles=='No vehicles identified':
        vehicles = None
    else:
        vehicles=misc.html_table(vehicles,True)
    return render_template('homepage.html', vehicles=vehicles)

@app.route('/vehicles', methods=['GET','POST'])
@login_required
@check_confirmed
def vehicles(): 
    error = None
    #check that id is registered to user. If not, return forbidden
    if users.ValidIDforUser(session['username'], request.args.get('id'))==False:
        flash("The requested vehicle is not linked to your account")
        return redirect(url_for('index'))
    #render_template('homepage.html', error=error)
    else:
        if request.method == 'POST':
            id=request.args.get('id')
            r={}
            r['result']=False
            r['reason']='Unknown error'
            if "acon" in request.form:
                r=users.SendCommand(session['username'],id,'command/auto_conditioning_start')
            elif "acoff" in request.form:
                r=users.SendCommand(session['username'],request.args.get('id'),'command/auto_conditioning_stop')
            elif "stopcharge" in request.form:
                r=users.SendCommand(session['username'],request.args.get('id'),'command/charge_stop')
            elif "startcharge" in request.form:
                r=users.SendCommand(session['username'],request.args.get('id'),'command/charge_start')
            elif "threshold" in request.form:
                msg=request.form["threshold"]
            else:
                users.UpdateThreshold(str(request.args.get("id")),int(request.json))
                msg=str(request.json)+"~"+str(request.args.get("id"))
                return jsonify(msg)
            if r['result']:
                msg="Comand successful"
            else:
                msg="Error: "+r['reason']
            flash(msg)
            return redirect(url_for('vehicles')+"?id="+id)
        elif request.method == 'GET':  
            id=request.args.get('id')
            sql=f'''SELECT threshold FROM managedcharging WHERE id='{id}' LIMIT 1;'''
            result=users.ExecSQL(sql)
            if len(result)==0:
                priorthresh=50
            else:
                priorthresh=result[0][0]
            info=users.VehicleInfo(session['username'],id)
            charge={}
            charge['Battery Level']=str(info['charge_state']['battery_level'])+'%'
            charge['Battery Range']=str(int(info['charge_state']['battery_range']))+str(info['gui_settings']['gui_distance_units'])[0:str(info['gui_settings']['gui_distance_units']).find('/')]
            charge['Charge State']=info['charge_state']['charging_state']
            charge['Charge Limit']=str(info['charge_state']['charge_limit_soc'])+'%'
            if charge['Charge State']=='Charging':
                charge['Charge Rate']= str(info['charge_state']['charger_power'])+str(info['gui_settings']['gui_charge_rate_units'])
                charge['Charge Speed']= str(info['charge_state']['charge_rate'])+str(info['gui_settings']['gui_distance_units'])
    
            is_far=(info['gui_settings']['gui_temperature_units']=='F')
            climate={}
            climate['Temperature']=misc.Degrees(info['climate_state']['inside_temp'],is_far)
            climate['Outside Temperature']=misc.Degrees(info['climate_state']['outside_temp'],is_far)
            if info['climate_state']['is_climate_on']==True:
                climate['Air Conditioning']='On'
            else:
                climate['Air Conditioning']='Off'
            
            lat=info['drive_state']['latitude']
            long=info['drive_state']['longitude']
            loc=f'''<iframe width="600" height="450" frameborder="0" style="border:0"
                src="https://www.google.com/maps/embed/v1/place?key={google_api_key}&q={lat},{long}" allowfullscreen>
                </iframe>'''   
            return render_template('vehicles.html',error=error, info=info, loc=loc, charge=charge, climate=climate, priorthresh=priorthresh)

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

if __name__ == "__main__":
    app.run(debug=config.flask_debug,host='0.0.0.0', port=80)
