"""Manages the database. Each company will have a banner and text [file]
   that will be"""

import sqlite3
import sys

try:
    import Crypto
    sys.modules['crypto'] = Crypto
except:
    import crypto

from crypto.Cipher import AES

import base64
import os

DBNAME = 'SICP.db' #Student Internship Connection Program
BLOCK_SIZE = 32 #block size for cipher object
PADDING = '{' #ensures encrypted value is multiple of block size
SECRET = '3\xe2^m\xadD\xfe\xd1E*T]Hh\x06\xf6\x91\x07t)\xe9VkX\xa9\x8e\xeb\x1ep\xe8+\xea'

#make a dateactive attribute to make sure companies log on
#update TRAITS and PARAMS to ensure things work
COMPANYTNAME = 'Companies'
COMPANYTRAITS = '(name text, password text, cid int primary key, active integer, email text)'
COMPANYPARAMS = '(?, ?, ?, ?, ?)'

STUDENTTNAME = 'Students'
STUDENTTRAITS = '(name text, password text, sid int primary key, email text, intarray text)'
STUDENTPARAMS = '(?, ?, ?, ?, ?)'

INTERNSHIPTNAME = 'Internships'
INTERNSHIPTRAITS = '(name text, iid int primary key, cid int, active int)'
INTERNSHIPPARAMS = '(?, ?, ?, ?)'

def pad_text(s):
    """pads text to be encrypted"""
    return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

def encodeAES(c, pw):
    return base64.b64encode(c.encrypt(pad_text(pw)))

def create_db():
    """Creates the company and student tables.
       Deletes them if they already exist. Change the TRAIT constants
       to create new tables with different attributes"""

    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    #create tables "Companies"
    c.execute('DROP TABLE IF EXISTS {}'.format(COMPANYTNAME))
    c.execute('DROP TABLE IF EXISTS {}'.format(STUDENTTNAME))
    c.execute('DROP TABLE IF EXISTS {}'.format(INTERNSHIPTNAME))    

    c.execute('CREATE TABLE {} {}'.format(COMPANYTNAME, COMPANYTRAITS))
    c.execute('CREATE TABLE {} {}'.format(STUDENTTNAME, STUDENTTRAITS))
    c.execute('CREATE TABLE {} {}'.format(INTERNSHIPTNAME, INTERNSHIPTRAITS))

    conn.commit()
    conn.close()

    return

def add_company(name, password, email):
    """Creates unique id for each company, and adds company to the
       company table"""

    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    #get length    
    c.execute('SELECT name FROM {}'.format(COMPANYTNAME))

    ctnum = len(c.fetchall())
    
    #encrypt/encode text
    cipher = AES.new(SECRET)
    encoded = encodeAES(cipher, password)

    c.execute("INSERT INTO {} values {}".format(COMPANYTNAME, COMPANYPARAMS),
              (name, encoded, ctnum, 1, email))
    
    conn.commit()
    conn.close()

    return ctnum

def company_login(email, password):
    #check company's login information
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    cipher = AES.new(SECRET)

    c.execute('SELECT password FROM {} WHERE email = ?'.format(COMPANYTNAME),(email,))
    
    data = c.fetchone()
    if data is None:
        return False
    else:  
        encoded = encodeAES(cipher, password)
        if data[0] == encoded:
            return True
        else:
            return False

def add_student(name, password, email):
    """creates unique id for each student, and adds student to the
       student table"""

    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    #get length    
    c.execute('SELECT name FROM {}'.format(STUDENTTNAME))

    ctnum = len(c.fetchall())

    #encrypt/encode text
    cipher = AES.new(SECRET)
    encoded = encodeAES(cipher, password)

    internstring = "" #string will contain 0 for each entry in internship table
    for r in view_internship_t():
        internstring += '0'
    
    c.execute("INSERT INTO {} values {}".format(STUDENTTNAME, STUDENTPARAMS),
              (name, encoded, ctnum, email, internstring))
    
    conn.commit()
    conn.close()

    return ctnum

def student_login(email, password):
    #check company's login information
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    cipher = AES.new(SECRET)

    c.execute('SELECT password FROM {} WHERE email = ?'.format(STUDENTTNAME),(email,))
    data = c.fetchone()
    if data is None:
        return False
    else:
        encoded = encodeAES(cipher, password)
        if data[0] == encoded:
            return True
        else:
            return False

def add_internship(email, posname):
    """creates unique id for each internship, and adds internship to the
       internship table. Also updates each students intarray."""

    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    #get length    
    c.execute('SELECT name FROM {}'.format(INTERNSHIPTNAME))
    ctnum = len(c.fetchall())

    f_key = get_cid(email)

    #put position name, iid, and key to company table into internship table
    c.execute("INSERT INTO {} values {}".format(INTERNSHIPTNAME, INTERNSHIPPARAMS),
              (posname, ctnum, f_key, 1))

    #update each student's intarray with an appended 0
    for r in view_student_t():
        c.execute("UPDATE {} SET intarray='{}' WHERE sid='{}'".format(STUDENTTNAME, str(r[4]) + u"0", r[2]))
        
    conn.commit()
    conn.close()

    return ctnum

def get_cid(email):
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    c.execute("SELECT cid FROM {} where email is '{}'".format(COMPANYTNAME, email))
    data = c.fetchone()
    cid = data[0]
    
    conn.commit()
    conn.close()

    return cid

def get_sid(email):
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    c.execute("SELECT sid FROM {} where email is '{}'".format(STUDENTTNAME, email))
    data = c.fetchone()
    cid = data[0]
    
    conn.commit()
    conn.close()

    return cid

def get_cemail(iid):
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    
    c.execute('SELECT email FROM {} as C JOIN {} as I ON C.cid = I.cid'.format(COMPANYTNAME, INTERNSHIPTNAME))
    data = c.fetchone()

    conn.commit()
    conn.close()

    return data[0]

def check_ci_ids(cid, iid):
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    
    c.execute("SELECT cid FROM {} WHERE iid={}".format(INTERNSHIPTNAME, iid))
    data = c.fetchone()

    conn.commit()
    conn.close()
    
    if data[0] == cid:
        return True
    else:
        return False

def get_name(sid = None, iid=None):
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    sname, iname = None, None
    try:
        c.execute("SELECT name FROM {} WHERE sid={}".format(STUDENTTNAME, sid))
        data = c.fetchone()
        sname = data[0]
    except:
        pass
    
    try:
        c.execute("SELECT name FROM {} WHERE iid={}".format(INTERNSHIPTNAME, iid))
        data = c.fetchone()
        iname = data[0]
    except:
        pass

    conn.commit()
    conn.close()

    return sname, iname

def apply_student(email, iid):
    """Applies student, works directly with database"""
    iid = int(iid)
    
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    c.execute('SELECT sid, intarray FROM {} WHERE email is "{}"'.format(STUDENTTNAME, email))
    data = c.fetchone()

    sid = data[0]
    arr = data[1]
    try:
        arr[0]
    except:
        arr = str(arr)
        
    if arr[iid] == '0':
        arr = str(arr[0:iid] + "1" + arr[iid+1:len(arr)])
        c.execute('UPDATE {} SET intarray={} WHERE sid={}'.format(STUDENTTNAME, str(arr), sid))
    else:
        conn.commit()
        conn.close()
        return False
    
    conn.commit()
    conn.close()
    return True

def int_isactive(iid):
    iid = int(iid)
    
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    c.execute('SELECT active FROM {} WHERE iid={}'.format(INTERNSHIPTNAME, iid))
    data = c.fetchone()

    return data[0]

def int_makeinactive(iid):
    iid = int(iid)
    
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()
    c.execute('UPDATE {} SET active=0, name="", iid=-1, WHERE iid={}'.format(INTERNSHIPTNAME, iid))

    conn.commit()
    conn.close()

def student_seen(sid, iid):
    iid = int(iid)
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    c.execute('SELECT intarray FROM {} WHERE sid={}'.format(STUDENTTNAME, sid))
    data = c.fetchone()

    arr = data[0]
    arr = arr[0:iid] + "2" + arr[iid+1:len(arr)]
    c.execute('UPDATE {} SET intarray={} WHERE sid={}'.format(STUDENTTNAME, str(arr), sid))

    conn.commit()
    conn.close()

def get_jobs(sid):
    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    c.execute('SELECT intarray FROM {} WHERE sid={}'.format(STUDENTTNAME, sid))
    data = c.fetchone()
    arr = data[0]

    jobindices = []
    for i, c in enumerate(arr):
        if c == '1' or c == '2':
            jobindices.append(i)

    jobs = []
    for e in view_cjoini_t():
        if e[6] in jobindices:
            jobs.append(e)

    return jobs

########################################
##########VIEW TABLE FUNCTIONS##########
########################################

#this is a generator function!
def view_company_t():
    """yields each company's info as a generator"""

    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    for e in c.execute('SELECT * FROM {}'.format(COMPANYTNAME)):
        yield e
        
    conn.commit()
    conn.close()

#this is a generator function!
def view_student_t():
    """yields each student's info as a generator"""

    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    for e in c.execute('SELECT * FROM {}'.format(STUDENTTNAME)):
        yield e

    conn.commit()
    conn.close()

#this is a generator function!
def view_internship_t():
    """yields each student's info as a generator"""

    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    for e in c.execute('SELECT * FROM {}'.format(INTERNSHIPTNAME)):
        yield e

    conn.commit()
    conn.close()

def view_cjoini_t():
    """company name, comp password, company id, isactive, email,
       name of pos, internshipid, cid, internshipactive
       yields company join internships joined on cid"""

    conn = sqlite3.connect(DBNAME)
    c = conn.cursor()

    for e in c.execute('SELECT * FROM {} as C JOIN {} as I ON C.cid = I.cid'.format(COMPANYTNAME, INTERNSHIPTNAME)):
        yield e

    conn.commit()
    conn.close()
