from MySQLdb import IntegrityError
from werkzeug.utils import secure_filename
import os

from flask import Flask
from flask_mysqldb import MySQL
from flask import render_template, request, redirect, url_for,jsonify, make_response
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from models import UserProfile
import datetime
from flask import session
UPLOAD_FOLDER = "uploads"
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'school'
app.config['JSON_SORT_KEYS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
login_manager = LoginManager()
login_manager.init_app(app)
mysql = MySQL(app)
global User
User =  UserProfile(-4, "", "","")
  
import sys
###
# Routing for your application.
###


def get_all(who):
    try:
        cur = mysql.connection.cursor()
        cur.execute("select * from {};".format(who))
        dataset =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Database error getting {} '.format(who), 400)
    return dataset

def updateUserRegister_ID(who, userid):
    try:
        cur = mysql.connection.cursor()
        statement = "UPDATE {} SET User_ID = '{}'".format(who, userid)
        cur.execute(statement)
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return make_response('Database update  error ', 400)


@login_manager.user_loader
def load_user(user_id):
    return User

@app.route('/')
def home():
    return "flask is up and running"

@app.route('/login', methods=[ 'POST'])
def login():
    try:
        userID = request.json.get('UserID')
        password = request.json.get('Password')
    except Exception:
        return make_response("Incorrect json endpoints", 400)

     #check if valid   
     #get accounts
    try:
        cur = mysql.connection.cursor()
        cur.execute("select User_ID, Type from account where User_ID = '{}' and password = '{}';".format(userID, password))
        account =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Database error getting accounts', 400)
    
    if len(account) < 1:
        return make_response('Incorrect credentials', 400)

 
    type = account[0][1]
    


    #join and get
    try:
        cur = mysql.connection.cursor()
        cur.execute("select FirstName, LastName, account.User_ID from {},account where account.User_ID = {}.User_ID".format(type, type))
        account =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Database error join and find account', 400)

    print(account)
    global User
    User =  UserProfile(account[0][2], account[0][0], account[0][1], type) 
    print(type)
    login_user(User)
    return make_response("Successfully logged in {} {}".format(User.firstname, User.lastname))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return make_response('Succesfully logged out')

@app.route('/register', methods=['GET', 'POST'])
def Register():
    if request.method == 'POST':
        available = ["Student", "Lecturer", "Admin"]
        try:
            firstName = request.form.get('FirstName')
            middleName = request.form.get('MiddleName')
            lastName =  request.form.get('LastName')
            User_ID = request.form.get('User-ID')
            password = request.form.get('Password')
            type = request.form.get('TypeOfAccount')
        except Exception:
            return make_response("Incorrect form data", 400)
        
        if type not in available:
            return "TYPE NOT IN AVAILABLE"
        
        # Assuming get_all and updateUserRegister_ID functions are defined elsewhere
        dataset = get_all(type)

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM account;")
            accounts = cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Database error getting accounts', 400)

        for userid, _, _ in accounts:
            if userid == User_ID:
                return make_response('Two persons cannot have the same UserID', 400)

        for id, first, middle, last, _ in dataset:
            if first == firstName and middle == middleName and last == lastName:
                try:
                    cur = mysql.connection.cursor()
                    statement = "INSERT INTO account VALUES (%s, %s, %s)"
                    cur.execute(statement, (User_ID, password, type))
                    mysql.connection.commit()
                    cur.close()
                except Exception as e:
                    return make_response('Database insert account error', 400)
                
                try:
                    cur = mysql.connection.cursor()
                    statement = "INSERT INTO Register VALUES (%s, %s, %s)"
                    cur.execute(statement, (User_ID, id, datetime.datetime.today().strftime('%Y-%m-%d')))
                    mysql.connection.commit()
                    cur.close()
                except Exception as e:
                    return make_response('Database insert register error', 400)
                
                updateUserRegister_ID(type, User_ID)
                return make_response("Registered Successfully")

        return make_response("Information not found, please recheck!")

    return render_template('register.html')




@app.route('/create-course', methods=['POST'])
def createCourse():
    if User.type != "Admin" and not User.is_authenticated():
        return make_response("Must be an admin", 400)
    try:
        code = request.json.get('Course Code')
        title = request.json.get('Title')
        credit = request.json.get('Credits')
    except Exception:
        return make_response("Incorrect json endpoints", 400)

    
    try:
        cur = mysql.connection.cursor()
        statement = "INSERT INTO course VALUES('{}','{}',{})".format(code, title, credit)
        cur.execute(statement)
        mysql.connection.commit()
        cur.close()
    except  IntegrityError:
        return make_response('Course already exists', 400)

    except Exception as e:
        return make_response('Database course creation error ', 400)
    
    try:
        cur = mysql.connection.cursor()
        statement = "INSERT INTO Calendar(c_id) VALUES('{}')".format(code)
        cur.execute(statement)
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return make_response('Calendar creation error '+str(e), 400)
    
    return make_response("Course created sucessfulllyyyy")




@app.route('/retrieveALLcourses', methods=['GET'])
@login_required
def getallCourses():
    format = []
    courses = getAllCourses()
    
    for code, title, credit in courses:
        format.append({"Course Cose" : code, "Title" : title, "Credits" : credit})
    format.append({"Total Courses" : len(courses)})
    return make_response(jsonify(format))
  

@app.route('/assignLecturer/<lecid>', methods=['POST'])
@login_required
def assignLecturer(lecid):
    if User.is_authenticated():
        foundLec = False
        foundCourse = False
        try:
            cc = request.json.get('Course Code')
        except Exception:
            return make_response("Incorrect json endpoints", 400)


        #does lec exist?
        for id in getLecID():
            if (id[0] == lecid):
                foundLec = True
                break
        #does course exist?
        courses = getAllCourses()
        for code, _, _ in courses:
            if code == cc:
                foundCourse =True
                break

        #assign

        if foundLec and foundCourse:
            try:
                cur = mysql.connection.cursor()
                statement = "INSERT INTO assigned VALUES ('{}','{}')".format(cc, lecid)
                cur.execute(statement)
                mysql.connection.commit()
                cur.close()
            except Exception as e:
                return make_response('Database assigning lec error(assigning multiple lectures to a course maybe?) ', 400)
        else:
            return make_response("Lecturer or course not found", 400)
        return make_response("Assign Succesfull")
    return make_response("Must be an admin", 400)



@app.route('/registerStudent', methods=['POST'])
@login_required
def registerStudent():
    if User.type == "Student" and  User.is_authenticated():
        #does student exists?
    
        try:
            cc = request.json.get('Course Code')
        except Exception:
            return make_response("Incorrect json endpoints", 400)

        foundCourse = False

        courses = getAllCourses()
        for code, _, _ in courses:
            if code == cc:
                foundCourse =True
                break
        
        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT StudentID from student,account WHERE
        student.User_ID = account.User_ID and account.User_ID = '{}'
        """.format(User.id))
        idd =  cur.fetchall()
        cur.close()

        if  foundCourse:
            try:
                cur = mysql.connection.cursor()
                statement = "INSERT INTO StudentCourseReg(c_id, StudentID) VALUES ('{}','{}')".format(cc, idd[0][0])
                cur.execute(statement)
                mysql.connection.commit()
                cur.close()
            except Exception as e:
                return make_response('Database Register error ', 400)
        else:
            return make_response("Student or course not found", 400)
        return make_response("Registered Succesfully")
    return make_response("Must be Student!", 400)


@app.route('/getCourseS/<studid>', methods=['GET'])
@login_required
def getCourseS(studid):
    studfound = False
    if User.type == "Admin" and  User.is_authenticated():
        format = []
        #does stud exists?
        for id, *_ in getAllstudents():
            if id == studid:
                studfound = True
                break
        
        if studfound:
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                SELECT Course.CourseID, Title, Credits from Course, 
                (SELECT c_id from student, StudentCourseReg
                where student.StudentID = StudentCourseReg.StudentID and student.StudentID = '{}') as Students
                WHERE Course.CourseID = Students.c_id
                """.format(studid))
                courses =  cur.fetchall()
                cur.close()
            except Exception as e:
                return make_response('Error retrieving courses', 400)
            
            for code, title, credit in courses:
                format.append({"Course Cose" : code, "Title" : title, "Credits" : credit})
            format.append({"Total Courses" : len(courses)})
            return make_response(jsonify(format))
        else:
            return make_response("Wrong ID!", 400)

    return make_response("Must be Admin!", 400)


@app.route('/getCourseL/<lecid>', methods=['GET'])
@login_required
def getCourseL(lecid):
    if User.type == "Admin" and  User.is_authenticated():
        format = []
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT Course.CourseID, Title, Credits from Course, 
            (SELECT c_id from Lecturer, assigned
            where Lecturer.l_id = assigned.l_id and Lecturer.l_id = '{}') as Lecturers
            WHERE Course.CourseID = Lecturers.c_id
            """.format(lecid))
            courses =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving courses', 400)

        if len(courses) == 0:
            return make_response("No courses", 400)
        for code, title, credit in courses:
            format.append({"Course Cose" : code, "Title" : title, "Credits" : credit})
        format.append({"Total Courses" : len(courses)})
        return make_response(jsonify(format))
    return make_response("Must be Admin!", 400)



@app.route('/retrieveMembers/<code>', methods=['GET'])
@login_required
def retrieveMembers(code):
    if User.type == "Admin" and  User.is_authenticated():
        format = []
        #get lecturers
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            select FirstName, MiddleName, LastName from  Lecturer, assigned
            WHERE c_id = '{}' and Lecturer.l_id = assigned.l_id;
            """.format(code))
            lecs =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving lecturers', 400)
        format.append({"----------Lecturers----------" : ""})
        for f, m, l in lecs:
            format.append({"First Name" : f, "Middle Name" : m, "Last Name" : l})
        format.append({"Total Lecturers" : len(lecs)})

        #get Students
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            select FirstName, MiddleName, LastName from  student, studentcoursereg
            WHERE c_id = '{}' and student.StudentID = studentcoursereg.StudentID;
            """.format(code))
            studs =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving students', 400)
        format.append({"----------Students----------" : ""})
        for f, m, l in studs:
            format.append({"First Name" : f, "Middle Name" : m, "Last Name" : l})
        format.append({"Total Students" : len(studs)})

        return make_response(jsonify(format))
    return make_response("Must be Admin!", 400)


@app.route('/createEvent/<cc>', methods=['POST'])
@login_required
def createEvent(cc):
    if User.type == "Lecturer" and  User.is_authenticated():
        try:
            title = request.json.get('Title of Event')
            dueDate =  request.json.get('Due Date(dd/mm/yyyy)')
            month,day,year = dueDate.split('/')
            today =   datetime.date(int(year),int(month),int(day))
            print(today.strftime("%A, %d %b %Y"))

        except Exception:
            return make_response("Incorrect json endpoints", 400)
        
    
        try:
            cur = mysql.connection.cursor()
            cur.execute("select CalID FROM Calendar WHERE c_id = '{}'".format(cc))
            callids =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving Calendar', 400)
        if len(callids) == 0:
            return make_response("Incorrect Course Code", 400)
        
        
        try:
            cur = mysql.connection.cursor()
            statement = "INSERT INTO Calendarev VALUES ('{}','{}', '{}')".format(callids[0][0], title, today.strftime("%A, %d %b %Y"))
            cur.execute(statement)
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            return make_response('error creating Calendarev ', 400)
        return make_response("Event Creation Successful")
    return make_response("must be lecturer!", 400)



@app.route('/retrieveEvent/<cc>', methods=['GET'])
@login_required
def retrieveEvent(cc):
        if User.type == "Admin" and  User.is_authenticated():
            format = []
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
            select EventName, DueDate from Calendarev,Calendar
                where Calendar.CalID = Calendarev.CalID and c_id = '{}';
                """.format(cc))
                events =  cur.fetchall()
                cur.close()
            except Exception as e:
                return make_response('Error retrieving events', 400)

            if len(events) == 0:
                return make_response("No events!", 400)
            for name, due in events:
                format.append({"Event Title" : name, "Due Date" : due})
            format.append({"Total Events" : len(events)})
            return make_response(jsonify(format))
        else:
            return make_response("Must be admin", 400)



@app.route('/retrieveEventd', methods=['POST'])
@login_required
def retrieveEventd():
    #change to admin
    format = []
    try:
        id = request.json.get('StudentID')
        date =  request.json.get('Date(dd/mm/yyyy)')
        month,day,year = date.split('/')
        today =   datetime.date(int(year),int(month),int(day))
        

    except Exception:
        return make_response("Incorrect json endpoints", 400)
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
                select EventName, DueDate from calendarev,
                (select * from calendar,
                (SELECT Course.CourseID, Title, Credits from Course, 
                (SELECT c_id from student, StudentCourseReg
                 where student.StudentID = StudentCourseReg.StudentID and student.StudentID = '{}') as Students
                WHERE Course.CourseID = Students.c_id) as courses
                
                WHERE calendar.c_id = courses.CourseID) as calendars
                where calendarev.CalID = calendars.CalID and DueDate = '{}';
        """.format(id, today.strftime("%A, %d %b %Y")))
        events =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Error retrieving events', 400)
    if len(events) == 0:
        return make_response("No events!", 400)
    for name, due in events:
        format.append({"Event Title" : name, "Due Date" : due})
    format.append({"Total Events" : len(events)})
    print(today.strftime("%A, %d %b %Y"))
    return make_response(jsonify(format))

#might turn to endpoint
def getLecID():
    try:
        cur = mysql.connection.cursor()
        cur.execute("Select l_id from Lecturer, Account where Lecturer.User_ID = Account.User_ID;")
        lecids =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Error retrieving courses', 400)
    return lecids
    
    
@app.route('/createForum/<cc>', methods=['POST'])
@login_required
def createForum(cc):
    #change to lec
    foundCourse = False
    try:
        title = request.json.get('Forum Name')
        desc = request.json.get('Description')
    except Exception:
        return make_response("Incorrect json endpoints", 400)
    
    cur = mysql.connection.cursor()
    cur.execute("""
    SELECT l_id from Lecturer,account WHERE
    Lecturer.User_ID = account.User_ID and account.User_ID = '{}'
    """.format(User.id))
    idd =  cur.fetchall()
    cur.close()
    l_id = idd[0][0]
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT Course.CourseID FROM Course, 
        (SELECT c_id from Lecturer, assigned
        where Lecturer.l_id = assigned.l_id and Lecturer.l_id = '{}') as Lecturers
        WHERE Course.CourseID = Lecturers.c_id and Course.CourseID = '{}'
        """.format(l_id, cc))
        courses =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Error retrieving courses', 400)
    
    if len(courses >= 1):
        foundCourse = True
    if foundCourse:
        try:
            cur = mysql.connection.cursor()
            statement = "INSERT INTO forum(c_id, title, description, datecreated) VALUES ('{}','{}', '{}', '{}')".format(cc, title, desc, datetime.datetime.today().strftime('%Y-%m-%d'))
            cur.execute(statement)
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            return make_response('Database insert forum error ', 400)
    else:
        return make_response('Course dosent exist ', 400)
    return make_response("Course Successfully created")


@app.route('/retieveForum/<cc>', methods=['GET'])
@login_required
def retieveForum(cc):
    format = []
    #change to admin
    foundCourse = False
    courses = getAllCourses()
    for code, _, _ in courses:
        if code == cc:
            foundCourse =True
            break
    
    if foundCourse:
        try:
            cur = mysql.connection.cursor()
            cur.execute("select title, datecreated, description from forum where c_id = '{}';".format(cc))
            forums =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving courses', 400)
    
    if len(forums) == 0:
        return make_response("No forums!", 400)
    for title, datecreated, description in forums:
        format.append({"Title" : title, "Message" : description, "Date Created" : datecreated})
    format.append({"Total forums" : len(forums)})
    return make_response(jsonify(format))



@app.route('/createThread/<cc>', methods=['POST'])
@login_required
def createThread(cc):
    if User.is_authenticated:
        try:
            fi = request.json.get('Forum ID')
            title = request.json.get('Thread Title')
            desc = request.json.get('Message')
        except Exception:
            return make_response("Incorrect json endpoints", 400)
        

        courses = []
        
        

        if User.type == "Student":
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT StudentID from student,account WHERE
            student.User_ID = account.User_ID and account.User_ID = '{}'
            """.format(User.id))
            idd =  cur.fetchall()
            cur.close()
            s_id = idd[0][0]
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                SELECT Course.CourseID from Course, 
                (SELECT c_id from student, StudentCourseReg
                where student.StudentID = StudentCourseReg.StudentID and student.StudentID = '{}') as Students
                WHERE Course.CourseID = Students.c_id and Course.CourseID = '{}'
                """.format(s_id, cc))
                courses =  cur.fetchall()
                cur.close()
            except Exception as e:
                return make_response('Error retrieving courses', 400)
            

        elif User.type == "Lecturer":
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT l_id from Lecturer,account WHERE
            Lecturer.User_ID = account.User_ID and account.User_ID = '{}'
            """.format(User.id))
            idd =  cur.fetchall()
            cur.close()
            l_id = idd[0][0]
            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                SELECT Course.CourseID FROM Course, 
                (SELECT c_id from Lecturer, assigned
                where Lecturer.l_id = assigned.l_id and Lecturer.l_id = '{}') as Lecturers
                WHERE Course.CourseID = Lecturers.c_id and Course.CourseID = '{}'
                """.format(l_id, cc))
                courses =  cur.fetchall()
                cur.close()
            except Exception as e:
                return make_response('Error retrieving courses', 400)
            
        if len(courses) >=1:
                try:
                    cur = mysql.connection.cursor()
                    statement = "insert into discussion_thread(forum_id, title, datecreated, message, owner) values('{}', '{}', '{}', '{}', '{}')".format(fi, title, datetime.datetime.today().strftime('%Y-%m-%d'), desc, User.firstname +" "+User.lastname)
                    cur.execute(statement)
                    mysql.connection.commit()
                    cur.close()
                except Exception as e:
                    return make_response('Error creating thread ', 400)
        else:
            return make_response("Not a member of course", 400)
        return make_response("Thread successfully created")


    return make_response("LOGIN", 400)


    


@app.route('/retrieveThread/<fi>', methods=['GET'])
@login_required
def retrieveThread(fi):
    format = []
    if User.is_authenticated:
        try:
            cur = mysql.connection.cursor()
            cur.execute("select disc_id, title, datecreated, owner from discussion_thread where forum_id = '{}';".format(fi))
            threads =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving threads', 400)
        
        for disc_id, title, datecreated, owner in threads:
                    format.append({"Discussion ID" : disc_id, "Title" : title, "Date Created" : datecreated, "Owner" : owner})
        format.append({"Total Threads" : len(threads)})

        return make_response(format)
    return make_response("LOGIN", 400)


@app.route('/createContent/<cc>', methods=['POST'])
@login_required
def createContent(cc):
    #lecturer
    if User.is_authenticated:
        try:
            title = request.json.get('Section Title')
        except Exception:
            return make_response("Incorrect json endpoints", 400)
        
        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT l_id from Lecturer,account WHERE
        Lecturer.User_ID = account.User_ID and account.User_ID = '{}'
        """.format(User.id))
        idd =  cur.fetchall()
        cur.close()
        l_id = idd[0][0]
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT Course.CourseID FROM Course, 
            (SELECT c_id from Lecturer, assigned
            where Lecturer.l_id = assigned.l_id and Lecturer.l_id = '{}') as Lecturers
            WHERE Course.CourseID = Lecturers.c_id and Course.CourseID = '{}'
            """.format(l_id, cc))
            courses =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving courses', 400)
        
        if len(courses) >=1:
                try:
                    cur = mysql.connection.cursor()
                    statement = "insert into content(c_id, title) values('{}', '{}')".format(courses[0][0], title)
                    cur.execute(statement)
                    mysql.connection.commit()
                    cur.close()
                except Exception as e:
                    return make_response('Error creating content ', 400)
                return make_response("Content created sucessfully")
        else:
            make_response("Lecturer not assignment to course", 400)
    return make_response("LOGIN", 400)


@app.route('/retieveContent/<cc>', methods=['GET'])
@login_required
def retieveContent(cc):
    format = []
    if User.is_authenticated:
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT content.Title, content.cont_id from content, course where content.c_id = course.CourseID and course.CourseID = '{}';".format(cc))
            contents =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving threads', 400)
        
        if len(contents) == 0:
            return make_response("No content", 400)
        
        for title,id in contents:
                    format.append({"----------Section----------" :""})
                    format.append({ "Content ID" : id, "Title" : title})
                    cur = mysql.connection.cursor()
                    cur.execute("select item_id,contentitems.title,link_filepath from contentitems,content where contentitems.cont_id = content.cont_id and contentitems.cont_id = {};".format(id))
                    items =  cur.fetchall()
                    cur.close()
                    format.append({ "----------ITEMS----------":""})
                    for itid, contit, path in items:
                        format.append({ "Item ID" : itid, "Title" : contit, "Link/Path" : path})


        format.append({"Total Contents" : len(contents)})

        return make_response(format)
    return make_response("LOGIN", 400)


@app.route('/createItem/<cc>/<tit>', methods=['POST'])
@login_required
def createItem(cc, tit):
    #lecturer

    if User.is_authenticated() and User.type == "Lecturer":
        titlefound = False
        sectit = ""
        try:
        
                file = request.files['file']
                link =  request.form.get('link')
        except Exception:
            return make_response("Incorrect json endpoints", 400)
        

        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT l_id from Lecturer,account WHERE
        Lecturer.User_ID = account.User_ID and account.User_ID = '{}'
        """.format(User.id))
        idd =  cur.fetchall()
        cur.close()
        l_id = idd[0][0]
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT Course.CourseID FROM Course, 
            (SELECT c_id from Lecturer, assigned
            where Lecturer.l_id = assigned.l_id and Lecturer.l_id = '{}') as Lecturers
            WHERE Course.CourseID = Lecturers.c_id and Course.CourseID = '{}'
            """.format(l_id, cc))
            courses =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving courses', 400)
        if(len(courses) <1):
            return make_response("lecturer not assigned to course")

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT content.cont_id, content.title from content, course where content.c_id = course.CourseID and course.CourseID = '{}';".format(cc))
            contents =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving threads', 400)
        
        if len(contents) == 0:
            return make_response("Wrong code", 400)
        
        for title, realtit in contents:
            if int(title) == int(tit):
                titlefound = True
                sectit = realtit
                break

        if titlefound:

            filename = secure_filename(file.filename)
            if filename == "":
                try:
                    cur = mysql.connection.cursor()
                    statement = "INSERT INTO contentitems(cont_id, title, link_filepath) VALUES ('{}','{}', '{}')".format(tit,sectit, link)
                    cur.execute(statement)
                    mysql.connection.commit()
                    cur.close()
                except Exception as e:
                    return make_response('error creating content item ', 400)
            else:
                try:
                    cur = mysql.connection.cursor()
                    statement = "INSERT INTO contentitems(cont_id, title, link_filepath) VALUES ('{}','{}', '{}')".format(tit,sectit, filename)
                    cur.execute(statement)
                    mysql.connection.commit()
                    cur.close()
                    try:
                        file.save(os.path.join(cc+" "+sectit, filename))
                    except Exception as e:
                        os.makedirs(cc+" "+sectit)
                        file.save(os.path.join(cc+" "+sectit, filename))   
                            
                except Exception as e:
                    return make_response('error creating content item ', 400)
                
     
            
            return make_response("content item saved")
        else:
            return make_response("Incorrect id ", 400)

    return make_response("LOGIN", 400)


def getAllCourses():
    try:
        cur = mysql.connection.cursor()
        cur.execute("select * from course;")
        courses =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Error retrieving courses', 400)
    return courses


def getAllstudents():
    try:
        cur = mysql.connection.cursor()
        cur.execute("Select * from Student, Account where Student.User_ID = Account.User_ID;")
        students =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('Error retrieving courses', 400)
    return students




@app.route('/submit/<cc>', methods=['POST'])
@login_required
def submitAssignment(cc):
    if User.is_authenticated() and User.type == "Student":
        try:
            file = request.files['file']
            
        except Exception:
            return make_response("Insert a file!!!", 400)
        
        foundcourse = False
        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT StudentID from student,account WHERE
        student.User_ID = account.User_ID and account.User_ID = '{}'
        """.format(User.id))
        idd =  cur.fetchall()
        cur.close()
        s_id = idd[0][0]
       
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT Course.CourseID from Course, 
            (SELECT c_id from student, StudentCourseReg
            where student.StudentID = StudentCourseReg.StudentID and student.StudentID = '{}') as Students
            WHERE Course.CourseID = Students.c_id and Course.CourseID = '{}'
            """.format(s_id, cc))
            courses =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving courses', 400)

        if len(courses)< 1:
            return make_response("Wrong course code", 400)
        
        filename = secure_filename(file.filename)

        try:
            print(s_id)
            cur = mysql.connection.cursor()
            statement = "INSERT INTO Assignment(stud_id, files, dateSubmitted, CourseID) VALUES ('{}','{}', '{}', '{}')".format(s_id, filename, datetime.datetime.today().strftime('%Y-%m-%d'), cc)
            cur.execute(statement)
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            return make_response('error submitting assignment ', 400)
        try:
            file.save(os.path.join(cc+"Assignment"+User.firstname + " " +User.lastname, filename))
        except Exception as e:
            os.makedirs(cc+"Assignment"+User.firstname + " " +User.lastname)
            file.save(os.path.join(cc+"Assignment"+User.firstname + " " +User.lastname, filename))
        return make_response("assignment submitted")
    return make_response("LOGIN", 400)



@app.route('/giveGrade/<cc>', methods=['POST'])
@login_required
def submitGrade(cc):
    if User.is_authenticated and User.type == "Lecturer":
        try:
            ass = request.json.get('Assignment ID')
            grade = request.json.get('Grade')
        except Exception:
            return make_response("Incorrect json endpoints", 400)
        

        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT l_id from Lecturer,account WHERE
        Lecturer.User_ID = account.User_ID and account.User_ID = '{}'
        """.format(User.id))
        idd =  cur.fetchall()
        cur.close()
        l_id = idd[0][0]
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT Course.CourseID FROM Course, 
            (SELECT c_id from Lecturer, assigned
            where Lecturer.l_id = assigned.l_id and Lecturer.l_id = '{}') as Lecturers
            WHERE Course.CourseID = Lecturers.c_id and Course.CourseID = '{}'
            """.format(l_id, cc))
            courses =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving courses', 400)
        if(len(courses) <1):
            return make_response("lecturer not assigned to course")
        
        try:
            cur = mysql.connection.cursor()
            statement = "update assignment set grade = {} where ass_id = {} and CourseID = '{}'".format(grade, ass, cc)
            cur.execute(statement)
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            return make_response('update error ', 400)
    



    
@app.route('/getAssign/<cc>', methods=['GET'])
@login_required
def getGrade(cc):
    if User.is_authenticated and User.type == "Lecturer":
        format = []
  
        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT l_id from Lecturer,account WHERE
        Lecturer.User_ID = account.User_ID and account.User_ID = '{}'
        """.format(User.id))
        idd =  cur.fetchall()
        cur.close()
        l_id = idd[0][0]
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            SELECT Course.CourseID FROM Course, 
            (SELECT c_id from Lecturer, assigned
            where Lecturer.l_id = assigned.l_id and Lecturer.l_id = '{}') as Lecturers
            WHERE Course.CourseID = Lecturers.c_id and Course.CourseID = '{}'
            """.format(l_id, cc))
            courses =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('Error retrieving courses', 400)
        if(len(courses) <1):
            return make_response("lecturer not assigned to course")
        
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
            select student.StudentID, student.FirstName, student.MiddleName, student.LastName, assignment.ass_id , assignment.files
            from assignment, student
            where student.StudentID = assignment.stud_id and CourseID = '{}';
            """.format(cc))
            ass =  cur.fetchall()
            cur.close()
        except Exception as e:
            return make_response('update error ', 400)
        
        for studid, first, mid, last, assid, files in ass:
            format.append({"Student ID" : studid, "FirstName" : first, "Middle Name" : mid, "Last Name" : last, "Assignment ID" : assid, "File" : files})
        format.append({"Total Assignments" : len(ass)})
        return make_response(jsonify(format))
    return make_response("LOGIN", 400)



@app.route('/getCourse>50', methods=['GET'])
def getNumS50():
    format = []
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
        select CourseID, count(studentcoursereg.StudentID) as numStudents
        from course, studentcoursereg
        where course.CourseID = studentcoursereg.c_id
        group by CourseID;
        """)
        stud =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('error getting All courses that have 50 or more students ', 400)
    #view
    try:
        cur = mysql.connection.cursor()
        statement = """
         CREATE OR REPLACE VIEW 50students AS 
        select CourseID, count(studentcoursereg.StudentID) as numStudents
        from course, studentcoursereg
        where course.CourseID = studentcoursereg.c_id
        group by CourseID
        having numStudents > 0;
         """
        cur.execute(statement)
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return make_response('error creating views ', 400)

    
    
    for code, num in stud:
        format.append({"Course Cose" : code, "# of students" : num})


    return make_response(jsonify(format))



@app.route('/getStud>4', methods=['GET'])
def getStud4():
    format = []
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
        select student.StudentID, FirstName, MiddleName, MiddleName, COUNT(c_id) as numCourses 
        from student, studentcoursereg
        where student.StudentID = studentcoursereg.StudentID
        group by student.StudentID
        having numCourses > 0;
        """)
        stud =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('error getting All courses that have 50 or more students ', 400)
    #view
    try:
        cur = mysql.connection.cursor()
        statement = """
         CREATE OR REPLACE VIEW Report2 AS 
        select student.StudentID, FirstName, MiddleName, LastName, COUNT(c_id) as numCourses 
        from student, studentcoursereg
        where student.StudentID = studentcoursereg.StudentID
        group by student.StudentID
        having numCourses > 0;
         """
        cur.execute(statement)
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return make_response('error creating views ' , 400)

    
    
    for id, first,middle,last,num in stud:
        format.append({"Student ID" : id, "First Name" : first, "Middle Name" : middle, "LastName" : last, "#of Courses" : num})


    return make_response(jsonify(format))




@app.route('/Report3', methods=['GET'])
def Report3():
    format = []
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
        Select lecturer.l_id, count(c_id) as numCourses
        from lecturer, assigned
        where lecturer.l_id = assigned.l_id
        group by lecturer.l_id
        HAVING numCourses > 0;
        """)
        stud =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('error getting All courses that have 50 or more students ', 400)
    #view
    try:
        cur = mysql.connection.cursor()
        statement = """
         CREATE OR REPLACE VIEW Report3 AS 
        Select lecturer.l_id, count(c_id) as numCourses
        from lecturer, assigned
        where lecturer.l_id = assigned.l_id
        group by lecturer.l_id
        HAVING numCourses > 0;
         """
        cur.execute(statement)
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return make_response('error creating views ' , 400)

    
    
    for id, num in stud:
        format.append({"Lecturer ID" : id, "#of Courses" : num})


    return make_response(jsonify(format))



@app.route('/Report4', methods=['GET'])
def Report4():
    format = []
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
        select course.CourseID, Count(studentcoursereg.StudentID) as numStudent 
        from course, studentcoursereg
        where course.CourseID = studentcoursereg.c_id
        GROUP by course.CourseID
        having numStudent > 0;
        """)
        stud =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('error getting All courses that have 50 or more students ', 400)
    #view
    try:
        cur = mysql.connection.cursor()
        statement = """
         CREATE OR REPLACE VIEW Report4 AS 
        select course.CourseID, Count(studentcoursereg.StudentID) as numStudent 
        from course, studentcoursereg
        where course.CourseID = studentcoursereg.c_id
        GROUP by course.CourseID
        having numStudent > 0;
         """
        cur.execute(statement)
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return make_response('error creating views ' , 400)

    
    
    for id, num in stud:
        format.append({"Course Code " : id, "#of Students" : num})


    return make_response(jsonify(format))





@app.route('/Report5', methods=['GET'])
def Report5():
    format = []
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
        select assignment.stud_id,  avg(assignment.grade)As Average from assignment
        group by stud_id
        order by Average DESC
        limit 10;
        """)
        stud =  cur.fetchall()
        cur.close()
    except Exception as e:
        return make_response('error getting All courses that have 50 or more students ', 400)
    #view
    try:
        cur = mysql.connection.cursor()
        statement = """
         CREATE OR REPLACE VIEW Report5 AS 
            select assignment.stud_id,  avg(assignment.grade)As Average from assignment
            group by stud_id
            order by Average DESC
            limit 10;
         """
        cur.execute(statement)
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        return make_response('error creating views ' , 400)

    
    
    for id, num in stud:
        format.append({"Student ID " : id, "Average" : num})


    return make_response(jsonify(format))
