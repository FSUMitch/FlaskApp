import sqlite3
import database as adb
import os
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

from flask import Flask, flash, render_template, request, url_for, redirect, \
     g, escape, session, send_from_directory
from werkzeug import secure_filename

#init stuff
DATABASE = 'SICP.db'
PORT = 5003
DEBUG = True

LOGO_FOLDER = r'./static/images/'
UPLOAD_FOLDER = r'/home/icsfsu/FlaskApp/uploads/'
DESC_FOLDER = r'./database/descs/'
RESUME_FOLDER = r'./database/resumes/'
ALLOWED_IMG_EXT = set(['png', 'jpg', 'jpeg', 'gif'])
ALLOWED_TXT_EXT = set(['txt', 'doc', 'docx'])

app = Flask(__name__)
app.config['LOGO_FOLDER'] = LOGO_FOLDER
app.config['LOGO_ACCESS'] = LOGO_FOLDER
app.config['DESC_FOLDER'] = DESC_FOLDER
app.config['RESUME_FOLDER'] = RESUME_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 #limit for image files
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
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/uploads/<path:filename>')
def fileResume(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/descriptions/<path:filename>')
def fileDesc(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/')
def main():
    app.logger.debug('Main page accessed')
    return render_template('index.html')

@app.route('/SICP')
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

@app.route('/SCIP')
def fix():
    return redirect('/SICP')

@app.route('/Employer')
def fixE():
    return redirect('Employers')

@app.route('/Student')
def fixS():
    return redirect('/Students')

@app.route('/Student/MyApplications')
def fixJ():
    return redirect('/Students/View')

@app.route('/logout')
def logout():
    session.clear()

    return redirect('SCIP')
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
    if escape(session.get('type')) == 'student':
        table=[(i[0], i[4], i[5], i[6], os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'],
                                                  "desc{}.txt".format(i[6]))), is_imgfile(i[2]), i[2]) for i in adb.view_cjoini_t() if i[8]]
        if request.method == 'POST':#once we have search fields
            return render_template('studentsearch.html')
        else:
            return render_template('studentsearch.html',
                        table=table,
                        desc=True)


    return redirect('/Students')

@app.route('/Student/Apply/<iid>')
def studentApply(iid):
    if escape(session['type']) == 'student':
        email = escape(session['uname']) #email of logged in student
        if adb.int_isactive(iid) and adb.apply_student(email, iid): #if success, (hasn't already applied)
            sid = adb.get_sid(email)
            toemail = adb.get_cemail(iid)
            send_email(sid, iid, toemail, email)
            flash('You have successfully applied to this internship!')
            return redirect("/Student/Search")

        elif not adb.int_isactive(iid):
            flash('Could not apply to this internship.')
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
            if get_txtfile(sid):
                #txtfile = open(get_txtfile(sid))
                return render_template('studenteditresume.html', sid=sid, ext=get_txtext(get_txtfile(sid)))
            else:
                return render_template('studentaddresume.html')


        if request.method == 'POST':
            #use the logged in uname(email) and position name
            #to create position in db module
            sid = adb.get_sid(escape(session['uname']))
            txtfile = request.files['txt_file']
            if txtfile and allowed_text(txtfile.filename):
                fname = "resume{}.{}".format(sid, get_txtext(txtfile.filename))
                txtfile.save(os.path.join(app.config['UPLOAD_FOLDER'],
                                          fname))
                flash("Successfully added your resume!")
                return redirect('/Student/Home')

            else:
                flash("Could not add your resume")
                return redirect('/Student/Home')

    return redirect('/Student')

@app.route('/Student/View')
def studentViewApps():
    if escape(session['type']) == 'student':
        email = escape(session['uname']) #email of logged in student

        sid = adb.get_sid(escape(session['uname']))
        jobs = adb.get_jobs(sid)

        table=[(i[0], i[4], i[5], i[6],
                os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'],
                               "desc{}.txt".format(i[6]))),
                is_imgfile(i[2]), i[2]) for i in jobs if i[8]]

        return render_template('studentview.html', table=table)

    return redirect('/Student')

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

            imgfile = request.files['img_file']
            if imgfile and allowed_image(imgfile.filename):
                cid = adb.get_cid(escape(session['uname']))
                fname = "logo{}.{}".format(cid, 'jpg')
                imgfile.save(os.path.join(app.config['UPLOAD_FOLDER'],
                                          fname))
                flash("Successfully added your logo!")

            else:
                flash("Could not add logo")

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
            if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'],
                                              "logo{}.jpg".format(cid))):
                return render_template('employereditlogo.html',
                                       imgpath=app.config['UPLOAD_FOLDER'] +
                                            "logo{}.jpg".format(cid), cid=cid)
            else:
                return render_template('employeraddlogo.html', cid=cid)


        if request.method == 'POST':
            #use the logged in uname(email) and position name
            #to create position in db module
            cid = adb.get_cid(escape(session['uname']))
            imgfile = request.files['img_file']
            if imgfile and allowed_image(imgfile.filename):
                fname = "logo{}.{}".format(cid, 'jpg')
                imgfile.save(os.path.join(app.config['UPLOAD_FOLDER'],
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
                    fname = "desc{}.{}".format(iid, "txt")
                    txtfile.save(os.path.join(app.config['UPLOAD_FOLDER'],
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
    if escape(session['type']) == 'employer':
        sid = request.args.get('sid')
        iid = request.args.get('iid')

        cid = adb.get_cid(escape(session['uname']))
        if sid and iid:
            if adb.check_ci_ids(cid, iid):
                adb.student_seen(sid, iid)
                flash('Student has been removed.')
                return redirect('/Employer/ViewInternships/{}'.format(iid))

        internlist = []
        for r in adb.view_cjoini_t():
            if r[2] == cid and r[8]:
                internlist.append(r)

        return render_template('employerviewinternships.html', internlist=internlist)

    return 'employer'

@app.route('/Employer/ViewInternships/<iid>')
def employerViewSpecificInt(iid):
    if escape(session['type']) == 'employer':
        cid = adb.get_cid(escape(session['uname']))

        if adb.check_ci_ids(cid, iid):
            studs = students_applied(iid)
            sname, iname = adb.get_name(iid=iid)

            return render_template('employerviewinternshipsiid.html', students=studs, iid=iid, posname=iname)

    return redirect('/Employer')

@app.route('/Employer/View/<sid>')
def employerViewResume(sid):
    if escape(session['type']) == 'employer':
        try:
            return render_template('employerviewresume.html', sid=sid, ext=get_txtext(get_txtfile(sid)))
        except:
            flash('Could not open resume')
            return render_template('employerviewinternships.html')

    return redirect('Employer')

@app.route('/Employer/ViewInternships/ChangeDescription/<iid>', methods=['POST', 'GET'])
def employerChangeDescription(iid):
    if escape(session['type']) == 'employer':
        cid = adb.get_cid(escape(session['uname']))

        if adb.check_ci_ids(cid, iid):
            if request.method == 'GET':
                if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'],
                                                  "desc{}.txt".format(iid))):
                    txtfile = open(os.path.join(app.config['UPLOAD_FOLDER'],
                                              "desc{}.txt".format(iid)))

                    return render_template('employereditdescription.html',
                                           txt=txtfile.read())
                else:
                    return render_template('employeradddescription.html')


            if request.method == 'POST':
                #use the logged in uname(email) and position name
                #to create position in db module
                txtfile = request.files['txt_file']
                if txtfile and allowed_text(txtfile.filename):
                    fname = "desc{}.{}".format(iid, 'txt')
                    txtfile.save(os.path.join(app.config['UPLOAD_FOLDER'],
                                              fname))
                    flash("Successfully added your description!")
                    return redirect('/Employer/ViewInternships')

                else:
                    flash("Could not add your description.")
                    return redirect('/Employer/ViewInternships')

    return redirect('/Employer')

@app.route('/Employer/ViewInternships/Delete/<iid>')
def employerDeleteInt(iid):
    if escape(session['type']) == 'employer':
        cid = adb.get_cid(escape(session['uname']))

        if adb.check_ci_ids(cid, iid) and adb.int_isactive(iid):
            adb.int_makeinactive(iid)
            flash("Deleted your internship.")
            return redirect('/Employer/ViewInternships')

    return redirect('/Employer')
#####Non-routing functions#####

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

def get_txtfile(sid): #returns path of text file
    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], "resume{}.txt".format(sid))):
        return os.path.join(app.config['UPLOAD_FOLDER'], "resume{}.txt".format(sid))

    elif os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], "resume{}.doc".format(sid))):
        return os.path.join(app.config['UPLOAD_FOLDER'], "resume{}.doc".format(sid))

    elif os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], "resume{}.docx".format(sid))):
        return os.path.join(app.config['UPLOAD_FOLDER'], "resume{}.docx".format(sid))

    else:
        return False

def get_txtext(filename):
    return filename.rsplit('.', 1)[1]


def is_imgfile(iid):
    jpg = os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'],
                               "logo{}.jpg".format(iid)))
    png = os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'],
                               "logo{}.png".format(iid)))
    gif = os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'],
                               "logo{}.gif".format(iid)))

    return jpg or png or gif

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

def students_applied(iid):
    students = []
    for r in adb.view_student_t():
        if r[4][int(iid)] == '1':
            students.append(r)

    return students

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_IMG_EXT

def allowed_text(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_TXT_EXT

def send_email(sid, iid, to, cc,
               smtpserver='smtp.gmail.com:587'):
    from_addr = "sicp.ad.2015@gmail.com"
    login = "sicp.ad.2015@gmail.com"
    password = "asdfq3495"
    subject = "SICP Application Received"
    #to = "sicp.ad.2015@gmail.com"

    sname, iname = adb.get_name(sid, iid)
    message = """Hello,\nAn applicant, {}, has applied to your position {}. Please review this application on your home page.\n\nThank you,\nSICP Administration""".format(sname, iname)

    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP(smtpserver)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(login, password)
    text = msg.as_string()
    problems = server.sendmail(from_addr, to, text)
    server.quit()

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
    app.run(port=PORT, debug=False)
