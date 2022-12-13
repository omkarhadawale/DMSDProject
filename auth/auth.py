import json
import re
from turtle import pd
from flask import Blueprint, render_template, flash, redirect, url_for,current_app, session
import pyodbc
from auth.forms import AddReader, ChangeUserPassword, LoginForm, RegisterForm, UserProfileEdit
from sql.db import DB

from flask_login import login_user, login_required, logout_user
from auth.models import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

from flask_principal import Identity, AnonymousIdentity, \
     identity_changed

auth = Blueprint('auth', __name__, url_prefix='/',template_folder='templates')


@auth.route("/register", methods=["GET","POST"])
def register():
    form = RegisterForm()
    # wtform validators are both client-side and server-side
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        try:
            hash = bcrypt.generate_password_hash(password)
            # save the hash, not the plaintext password
            result = DB.insertOne("INSERT INTO IS601_Users (username, email, password) VALUES (%s, %s, %s)", username, email, hash)
            if result.status:
                flash("Successfully registered","success")
        except Exception as e:
            #UCID:-oh45
            if re.search(f"Duplicate entry",str(e)):
                if re.search(f"{email}",str(e)):
                    flash(f"{email} is not available(Email is already registered)","warning")
                if re.search(f"{username}",str(e)):
                    flash(f"Username:-{username} is already taken","warning")
            else:
                flash(str(e), "danger")
    return render_template("register.html", form=form)

@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        try:
            result = DB.selectOne("SELECT id, username, email, password FROM IS601_Users where email=%s", email)
            if result.status and result.row:
                hash = result.row["password"]
                if bcrypt.check_password_hash(hash, password):
                    from roles.models import Role
                    del result.row["password"] # don't carry password/hash beyond here
                    user = User(**result.row)
                    # get roles
                    result = DB.selectAll("""
                    SELECT name FROM IS601_Roles r JOIN IS601_UserRoles ur on r.id = ur.role_id WHERE ur.user_id = %s AND r.is_active = 1 AND ur.is_active = 1
                    """, user.id)
                    if result.status and result.rows:
                        print("role rows", result.rows)
                        user.roles = [Role(**r) for r in result.rows]
                    print(f"Roles: {user.roles}")
                    success = login_user(user) # login the user via flask_login
                    
                    if success:
                        # Tell Flask-Principal the identity changed
                        identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(user.id))
                        # store user object in session as json
                        session["user"] = user.toJson()
                        flash("Log in successful", "success")
                        return redirect(url_for("auth.landing_page",))
                    else:
                        flash("Error logging in", "danger")
                else:
                    flash("Invalid password", "warning")
            else:
                # invalid user and invalid password together is too much info for a potential attacker
                # normally we return a single message for both "invalid username or password" so an attacker doens't know which part was correct
                flash("Invalid user", "warning")

        except Exception as e:
            #UCID:-oh45
            if re.search("object has no attribute 'row'",str(e)):
                flash("The email is not registered", "warning")
            else:
                flash(str(e), "danger")   
    return render_template("login.html", form=form)

@auth.route("/landing-page", methods=["GET","POST"])
@login_required
def landing_page():
    #UCID:-oh45
    #Accessing logged In user from session
    user = json.loads(session["user"])
    #UCID:-oh45
    #Prefilling user profile edit form from session data
    userform = UserProfileEdit(obj=User(user['id'],user['username'],user['email'],user['roles']))
    passform = ChangeUserPassword()
    if userform.validate_on_submit():
        username = userform.username.data
        email = userform.email.data
        update = True
        if username == user['username'] and email==user['email']:
            update = False
        if update:
            try:
                result = DB.insertOne("UPDATE IS601_Users set username = %s, email = %s WHERE email = %s", username, email, user['email'])  
                if result.status:
                    flash("User profile successfully updated","success")
                    # UCID:-oh45
                    # Updating session 
                    newuser = {"id":user['id'],"username":username,"email":email,"roles":user['roles']}
                    print(newuser)
                    try:
                        usr = User(**newuser)
                        session["user"] = usr.toJSON()
                    except Exception as e:
                        flash("Their was an error updating user session","danger")
                        flash(f"Error message:-{str(e)}","danger")    
            except Exception as e:
            #UCID:-oh45
                if re.search(f"Duplicate entry",str(e)):
                    if re.search(f"{email}",str(e)):
                        flash(f"{email} is not available(Email is already registered)","warning")
                    if re.search(f"{username}",str(e)):
                        flash(f"Username:-{username} is already taken","warning")
                else:        
                    flash("Theie was an error updating username/email","danger")
                    flash(f"Error message:- {str(e)}","danger")
    #UCID:-oh45
    if passform.validate_on_submit():        
        oldpassword = passform.oldpassword.data
        newpassword = passform.newpassword.data
        try:
            result = DB.selectOne('SELECT password FROM IS601_Users where email=%s',user['email'])
            if result.status and result.row:
                if bcrypt.check_password_hash(result.row['password'], oldpassword):
                    try:
                        hash = bcrypt.generate_password_hash(newpassword)
                        result1 = DB.insertOne('UPDATE IS601_Users SET password=%s where email=%s', hash, user['email'])
                        if result1.status:
                            flash("Password successfully updated","success")
                    except Exception as e:
                        flash("Their was an error updating the user","danger")
                        flash(f"Error message:-{str(e)}","danger")    
                else:
                    flash("Wrong old password (please enter correct password)","warning")        
        except Exception as e:
            flash("Their was an error updating the password")
            flash(f"Error message:-{str(e)}","danger")
    return render_template("landing_page.html", form=userform, form1=passform)

@auth.route("/logout", methods=["GET"])
def logout():
    logout_user()
    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
    flash("Successfully logged out", "success")
    return redirect(url_for("auth.login"))


@auth.route('/addReader', methods=['GET','POST'])
@login_required
def addReader():
    addRform =  AddReader()
    if addRform.validate_on_submit():
        RNAME = addRform.RNAME.data
        RTYPE  = addRform.RTYPE.data
        ADDRESS = addRform.ADDRESS.data
        PHONE_NO = addRform.PHONE_NO.data

        conn_str = (
        r'DRIVER={SQL Server};'
        r'SERVER=Omkar;'
        r'DATABASE=OPR;'
        r'Trusted_Connection=yes;')
        cnxn = pyodbc.connect(conn_str)
        print("connection established")
        # cursor = cnxn.cursor()
        try:
            cursor = cnxn.cursor()
            data = cursor.execute(f"INSERT INTO READER VALUES(LEFT(NEWID(),10),'{RTYPE}','{RNAME}','{ADDRESS}','{PHONE_NO}')").commit()
            flash("Reader added Successfully","success")
            
        except Exception as e:
            flash(f"Error message{str(e)}","danger")
            flash("Their was error retriving","warning")
    
    return render_template("addReader.html", form=addRform)

@auth.route('/addDocument', methods=['GET'])
@login_required
def addDocument():
    
    
    
    flash("Add document","success")
    return redirect(url_for("sample.list"))   