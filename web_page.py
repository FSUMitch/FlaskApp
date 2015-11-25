"""
    WISHLIST:
        IMMEDIATE:
            Upload files
        NOT:
            Change Current Students redirect
            Implement 'remember me' (not forgot your password?)
            Admin Account?
"""

import sqlite3
import database as adb
import os

from flask import Flask, flash, render_template, request, url_for, redirect, \
     g, escape, session, send_from_directory

#init stuff
DATABASE = 'SCIP.db'
PORT = 5003
DEBUG = True
LOGO_FOLDER = r'.\static\images'
DESC_FOLDER = r'.\database\descs'
RESUME_FOLDER = r'.\database\resumes'
ALLOWED_IMG_EXT = set(['png', 'jpg', 'jpeg', 'gif'])
ALLOWED_TXT_EXT = set(['txt', 'doc', 'docx'])

app = Flask(__name__)
app.config['LOGO_FOLDER'] = LOGO_FOLDER
app.config['LOGO_ACCESS'] = r'/static/images/'
app.config['DESC_FOLDER'] = DESC_FOLDER
app.config['RESUME_FOLDER'] = RESUME_FOLDER
app.secret_key = "asdfq3495basdfbsdpo2451"



#################################
#############WEBPAGE#############
#################################

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['RESUME_FOLDER'],
                               filename)

@app.route('/')
def main():
    session.clear()
    app.logger.debug('Main page accessed')
    return render_template('index.html')

@app.route('/SCIP')
def choice():
    app.logger.debug('Main page accessed')

    try:
        if escape(session['type']) == 'student':
            return redirect('/Student/Home')
        if escape(session['type']) == 'employer':
            return redirect('/Employer/Home')
    except:
        pass
    
    return render_template('choice.html')

#######################
#####Student pages#####
#######################

@app.route('/Students')
def student():
    try:
        if escape(session['type']) == 'student':
            return redirect('/Student/Home')
    except:
        pass

    return render_template('students.html')

@app.route('/Student/Login', methods=['GET', 'POST'])
def studentLogin():
    try:
        if escape(session['type']) == 'student':
            return redirect('/Student/Home')
    except:
        pass
    
    error = None
    if request.method == 'POST':
        #valid_login not implemented
        if valid_login(request.form['email'],
                       request.form['password'],
                       True):
            session['uname'] = request.form['email']
            session['type']  = "student"
            return redirect('/Student/Home')
        else:
            error = 'Invalid username/password'

    return render_template('studentlogin.html', error=error)

@app.route('/Student/Register', methods=['GET', 'POST'])
def studentRegister():
    try:
        if escape(session['type']) == 'student':
            return redirect('/Student/Home')
    except:
        pass
    
    error = None
    if request.method == 'POST':
        #valid_login not implemented

        #returns 0 if successful, 1 if username already taken
        #2 if passwords dont match up, 3 if email already taken/invalid
        flag = reg_student(request.form['first'] + ' ' + request.form['last'],
                            request.form['password'],
                            request.form['cpassword'],
                            request.form['email'])
        if not flag: #log in not implemented
            session['uname'] = request.form['email']
            session['type']  = 'student'
            return redirect('/Student/Home')
        elif flag == 1:
            error = 'Invalid username/password'
        elif flag == 2:
            error = 'Invalid e-mail'
        elif flag == 4:
            error = 'E-mail already in use!'

    return render_template('studentregister.html', error=error)

@app.route('/Student/Home')
def studentHome():
    try:
        if escape(session['type']) == 'student':
            return render_template('studenthome.html')
    except:
        pass
    
    return redirect('/Students')

@app.route('/Student/Search', methods=['GET', 'POST'])
def studentSearch():
    try:
        if escape(session['type']) == 'student':
            if request.method == 'POST':#once we have search fields
                return render_template('studentsearch.html')
            else: 
                return render_template('studentsearch.html',
                            table=[(i[0], i[4], i[5], "a", "b", i[6]) for i in adb.view_cjoini_t()])
    except:
        pass

    
    return redirect('/Students')

@app.route('/Student/Apply', methods=['POST'])
def studentApply():
    if escape(session['type']) == 'student':
        email = escape(session['uname']) #email of logged in student
        iid   = request.form['internshipid']
        
        if adb.apply_student(email, iid): #if success, (hasn't already applied)
            flash('You have successfully applied to this internship!')
            return redirect("/Student/Search")
        else: #student has already applied
            flash('You have already applied to this internship!', 'error')
            return redirect("/Student/Search")

    
    return escape(session['type'])

@app.route('/Student/Resume', methods=['GET', 'POST'])
def studentResume():
    if escape(session['type']) == 'student':
        if request.method == 'GET':
            sid = adb.get_sid(escape(session['uname']))
            if os.path.isfile(os.path.join(app.config['RESUME_FOLDER'],
                                              "resume{}.txt".format(sid))):
                txtfile = open(os.path.join(app.config['RESUME_FOLDER'],
                                              "resume{}.txt".format(sid)))
                return render_template('studenteditresume.html', txt=txtfile.read(), sid=sid)
            else:
                return render_template('studentaddresume.html')


        if request.method == 'POST':
            #use the logged in uname(email) and position name
            #to create position in db module 
            sid = adb.get_sid(escape(session['uname']))
            txtfile = request.files['txt_file']
            if txtfile and allowed_text(txtfile.filename):
                fname = "resume{}.{}".format(sid, 'txt')
                txtfile.save(os.path.join(app.config['RESUME_FOLDER'],
                                          fname))
                flash("Successfully added your resume!")
                return redirect('/Student/Home')

            else:
                flash("Could not add your resume")
                return redirect('/Student/Home')

    return request.method + ' student'

########################
#####Employee pages#####
########################

@app.route('/Employers')
def employer():
    try:
        if escape(session['type']) == 'employer':
            return redirect('/Employer/Home')
    except:
        pass
    
    return render_template('employers.html')

@app.route('/Employers/Login', methods=['GET', 'POST'])
def employerLogin():
    try:
        if escape(session['type']) == 'employer':
            return redirect('/Employer/Home')
    except:
        pass
    
    error = None
    if request.method == 'POST':
        #valid_login not implemented
        if valid_login(request.form['email'],
                       request.form['password'],
                       False):
            session['uname'] = request.form['email']
            session['type']  = "employer"
            return redirect('/Employer/Home') #log in not implemented
        else:
            error = 'Invalid username/password'

    return render_template('employerlogin.html', error=error)
        
@app.route('/Employers/Register', methods=['GET', 'POST'])
def employerRegister():
    try: #if already logged in as employer go straight to home
        if escape(session['type']) == 'employer':
            return redirect('/Employer/Home')
    except:
        pass
    
    error = None
    if request.method == 'POST':
        #returns 0 if successful, 1 if username already taken
        #2 if passwords dont match up, 3 if email already taken/invalid
        flag = reg_employer(request.form['username'],
                            request.form['password'],
                            request.form['cpassword'],
                            request.form['email'])

        if not flag: #log in not implemented
            session['uname'] = request.form['email']
            session['type']  = "employer"
            return log_employer_in('email')
        elif flag == 1:
            error = 'Invalid username/password'
        elif flag == 2:
            error = 'Invalid e-mail'
        elif flag == 3:
            error = 'Company or E-mail already in use!'

    return render_template('employerregister.html', error=error)

@app.route('/Employer/Home')
def employerHome():
    try:
        if escape(session['type']) == 'employer':
            return render_template('employerhome.html')
    except:
        pass
    
    return redirect('/Employers')

@app.route('/Employer/EditLogo', methods=['GET', 'POST'])
def employerEditLogo():
    if escape(session['type']) == 'employer':
        if request.method == 'GET':
            cid = adb.get_cid(escape(session['uname']))
            if os.path.isfile(os.path.join(app.config['LOGO_FOLDER'],
                                              "logo{}.jpg".format(cid))):
                return render_template('employereditlogo.html',
                                       imgpath=app.config['LOGO_ACCESS'] +
                                            "logo{}.jpg".format(cid))
            else:
                return render_template('employeraddlogo.html')


        if request.method == 'POST':
            #use the logged in uname(email) and position name
            #to create position in db module 
            cid = adb.get_cid(escape(session['uname']))
            imgfile = request.files['img_file']
            if imgfile and allowed_image(imgfile.filename):
                fname = "logo{}.{}".format(cid, 'jpg')
                imgfile.save(os.path.join(app.config['LOGO_FOLDER'],
                                          fname))
                flash("Successfully added your logo!")
                return redirect('/Employer/Home')

            else:
                flash("Could not add image file")
                return redirect('/Employer/Home')

    return 'employer'

@app.route('/Employer/AddInternships', methods=['GET', 'POST'])
def employerAddInt():

    try:
        if escape(session['type']) == 'employer':
            if request.method == 'POST':
                #use the logged in uname(email) and position name
                #to create position in db module 
                iid = adb.add_internship(session['uname'], request.form['posname'])
                txtfile = request.files['txt_file']
                if txtfile and allowed_text(txtfile.filename):
                    fname = "description{}.{}".format(iid, "txt")
                    txtfile.save(os.path.join(app.config['DESC_FOLDER'],
                                              fname))
                    flash("Successfully added your internship!")
                    return redirect('/Employer/Home')

                else:
                    flash("Could not add description file")
                    return redirect('/Employer/Home')
                
            return render_template('employeraddinternships.html')
    
    except:
        pass
    
    return redirect('/Employers')


@app.route('/Employer/ViewInternships')
def employerViewInt():
    return 'employer'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def valid_login(email, password, student = True):
    if student and adb.student_login(email, password):
        return True
    if not student and adb.company_login(email, password):
        return True

    return False
    
def log_employer_in(username):
    return redirect('/Employer/Home')

def log_student_in(username):
    return redirect('/Student/Home')

#need to check if email is a possible valid email
#need to have some checks on arguments
def reg_employer(name, password, cpassword, email):

    #return 1 if passwords not equal error
    if password != cpassword:
        return 1
    if '@' not in email:
        return 2
    for r in adb.view_company_t(): #companies can't have same name
        if name == r[0] or email == r[4]:
            return 3
    
    else:
        adb.add_company(name, password, email)
        return False


def reg_student(name, password, cpassword, email):

    #return 1 if passwords not equal error
    if password != cpassword:
        return 1
    if '@' not in email:
        return 2
    for r in adb.view_student_t(): #students cant have same email
        if email == r[4]:
            return 4  
    else:
        adb.add_student(name, password, email)
        return False

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_IMG_EXT

def allowed_text(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_TXT_EXT

####################################################
###########UTILITY DEBUGGING FUNCTIONS##############
####################################################

@app.route('/Admin/RecreateDB')
def adminDB():
    adb.create_db()
    return 'done'

@app.route('/Admin/ViewT')
def adminSType():
    return session['type']

@app.route('/Admin/ViewC')
def adminViewC():
    s = ""
    for r in adb.view_company_t():
        s += str(r) + '\n'

    return s

@app.route('/Admin/ViewS')
def adminViewS():
    s = ""
    for r in adb.view_student_t():
        s += str(r) + '\n'

    return s

@app.route('/Admin/ViewI')
def adminViewI():
    s = ""
    for r in adb.view_internship_t():
        s += str(r) + '\n'

    return s

if __name__ == "__main__":
    app.logger.setLevel(0)
    app.run(port=PORT, debug=True)
