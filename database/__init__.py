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

    for r in view_company_t():
        if r[4] == email:
            f_key = r[2]
            break

    #put position name, iid, and key to company table into internship table
    c.execute("INSERT INTO {} values {}".format(INTERNSHIPTNAME, INTERNSHIPPARAMS),
              (posname, ctnum, f_key, 1))

    #update each student's intarray with an appended 0
    for r in view_student_t():
        c.execute("UPDATE {} SET intarray='{}' WHERE sid='{}'".format(STUDENTTNAME, str(r[4]) + u"0", r[2]))
        
    conn.commit()
    conn.close()

    return ctnum

############################
#def edit_internship(name):#
############################

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
        arr = arr[0:iid] + "1" + arr[iid+1:len(arr)]
        c.execute('UPDATE {} SET intarray={} WHERE sid={}'.format(STUDENTTNAME, str(arr), sid))
    else:
        conn.commit()
        conn.close()
        return False
    
    conn.commit()
    conn.close()
    return True

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

