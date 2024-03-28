import random
import datetime

file = open("insertquery.sql", "w")

# Define the number of students, courses, and lecturers
num_students = 100000
num_courses = 200
num_lecturers = 50

numcourses = {}

# Define the maximum and minimum number of courses per student
max_courses_per_student = 6
min_courses_per_student = 3

# Define the minimum number of students per course
min_students_per_course = 10

# Define the maximum and minimum number of courses per lecturer
max_courses_per_lecturer = 5
min_courses_per_lecturer = 1

# Open a file for writing the account data
file.write("INSERT INTO account VALUES\n")
for user_id in range(1, num_students + num_lecturers + 1):
    if user_id <= num_students:
        role = "Student"
    else:
        role = "Lecturer"

    if user_id == num_students + num_lecturers:
        file.write("('{}', '{}', '{}');\n".format(f'UserID{user_id}', f'password{user_id}', role))
    else:
        file.write("('{}', '{}', '{}'),\n".format(f'UserID{user_id}', f'password{user_id}', role))

# Open a file for writing the student data
file.write("\nINSERT INTO Student(StudentID, FirstName, MiddleName, LastName, User_ID) VALUES\n")
for student_id in range(1, num_students + 1):
    numcourses[student_id] = random.randint(min_courses_per_student, max_courses_per_student)
    if student_id == num_students:
        file.write("('{}', '{}', '{}', '{}', '{}');\n".format(student_id, f'FirstName{student_id}', f'MiddleName{student_id}', f'LastName{student_id}', f'UserID{student_id}'))
    else:
        file.write("('{}', '{}', '{}', '{}', '{}'),\n".format(student_id, f'FirstName{student_id}', f'MiddleName{student_id}', f'LastName{student_id}', f'UserID{student_id}'))

# Open a file for writing the register data
file.write("\nINSERT INTO Register VALUES\n")
for user_id in range(1, num_students + num_lecturers + 1):
    if user_id <= num_students:
        role = "Student"
    else:
        role = "Lecturer"

    if user_id == num_students + num_lecturers:
        file.write("('{}', '{}', '{}');\n".format(f'UserID{user_id}', user_id, datetime.datetime.today().strftime('%Y-%m-%d')))
    else:
        file.write("('{}', '{}', '{}'),\n".format(f'UserID{user_id}', user_id, datetime.datetime.today().strftime('%Y-%m-%d')))

# Open a file for writing the course data
file.write("\nINSERT INTO course VALUES\n")
for coursecode in range(1, num_courses + 1):
    if coursecode == num_courses:
        file.write("('{}', '{}', {});\n".format(f'Comp{coursecode}', f'A Level COMP{coursecode}', random.randint(1, 3)))
    else:
        file.write("('{}', '{}', {}),\n".format(f'Comp{coursecode}', f'A Level COMP{coursecode}', random.randint(1, 3)))

# Open a file for writing the calendar data
file.write("\nINSERT INTO Calendar(c_id) VALUES\n")
for coursecode in range(1, num_courses + 1):
    if coursecode == num_courses:
        file.write("('{}');\n".format(f'Comp{coursecode}'))
    else:
        file.write("('{}'),\n".format(f'Comp{coursecode}'))

# Open a file for writing the student course registration data
file.write("\nINSERT INTO StudentCourseReg(c_id, StudentID) VALUES\n")
used = set()  # Using a set to ensure uniqueness
for studid in numcourses:
    for i in range(numcourses[studid]):
        num = random.randint(1, num_courses)
        while (f'Comp{num}', studid) in used:  # Check if the pair already exists
            num = random.randint(1, num_courses)
        used.add((f'Comp{num}', studid))
        if studid == num_students and numcourses[studid] - 1 == i:
            file.write("('{}', '{}');\n".format(f'Comp{num}', studid))
        else:
            file.write("('{}', '{}'),\n".format(f'Comp{num}', studid))

# Open a file for writing the lecturer data
file.write("\nINSERT INTO Lecturer VALUES\n")
for lecturer_id in range(num_students + 1, num_students + num_lecturers + 1):
    if lecturer_id == num_students + num_lecturers:
        file.write("('{}', '{}', '{}', '{}', '{}');\n".format(lecturer_id, f'FirstName{lecturer_id}', f'MiddleName{lecturer_id}', f'LastName{lecturer_id}', f'UserID{lecturer_id}'))
    else:
        file.write("('{}', '{}', '{}', '{}', '{}'),\n".format(lecturer_id, f'FirstName{lecturer_id}', f'MiddleName{lecturer_id}', f'LastName{lecturer_id}', f'UserID{lecturer_id}'))

# Generate insert statements for assigned courses
file.write("\n-- Insert statements for assigned courses\n")

for course_id in range(1, num_courses + 1):
    lecturer_id = f'LecturerID{random.randint(1, num_lecturers)}'
    
    if course_id == num_courses:
        file.write("INSERT INTO assigned(c_id, l_id) VALUES ('Comp{}', '{}');\n".format(course_id, lecturer_id))
    else:
        file.write("INSERT INTO assigned(c_id, l_id) VALUES ('Comp{}', '{}');\n".format(course_id, lecturer_id))

file.close()