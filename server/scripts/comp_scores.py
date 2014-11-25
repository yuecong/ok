# import pickle
# import app.models
#from datetime import datetime
# import json


# from google.appengine.ext.remote_api import remote_api_stub
# import getpass
# from google.appengine.ext import ndb


# def auth_func():
#   return (raw_input('Username:'), getpass.getpass('Password:'))

# remote_api_stub.ConfigureRemoteApi(None, '/_ah/remote_api', auth_func, 'ok-server.appspot.com')

# Enter the below code into a remote_api shell session. 

ASSIGN_NAME = 'Trends'
STUDENTS = []
GROUPS = []
GRADES = {}

def get_assign_key(name=ASSIGN_NAME):
    q = app.models.Assignment.query(app.models.Assignment.display_name == name)
    return q.fetch()[0].key

def get_comp_scores(name=ASSIGN_NAME):
    assign_key = get_assign_key(name)
    q = app.models.Submission.query(app.models.Submission.compScore != None)
    return q.fetch()

def get_groups(assign_key):
    q = app.models.Group.query(app.models.Group.assignment == assign_key)
    return q.fetch()

def get_group_id(email, groups):
    for group in groups:
        if ndb.Key('User', email) in group.members:
            return group.key

def get_grade(grade_key):
    q = app.models.Score.query(app.models.Score.key == grade_key)
    return q.fetch()

def write(grades):
    email_to_login = parse_email_file()
    with open(ASSIGN_NAME+'_Grades.txt','a') as the_file:
        for student in grades.keys():
            grade = grades[student]
            try:
                login = email_to_login[student]
                the_file.write(login + ' ' + str(grade[0])  +' ' +  grade[1] +' \n')
            except:
                print("Not found", student)

def parse_email_file():
    emails = open("emails.txt", "rb")
    email_to_login = {}
    for line in emails:
        line = line.decode('utf-8')
        parts = line.strip().split(',')
        email_to_login[parts[-1]] = parts[-2]
    emails.close()
    return email_to_login

assign_key = get_assign_key()
student_to_group = {}
for idx, val in enumerate(get_groups(assign_key)):
    GROUPS.append(val)
    for memb in val.members:
        student_to_group[memb] = idx

graded_subms = get_comp_scores()

for subm in graded_subms:
    score = subm.compScore
    url = 'https://ok-server.appspot.com/#/submission/'+str(subm.key.id())+'/diff'
    submitter = subm.submitter
    if submitter in student_to_group:
        group = student_to_group[submitter]
        group_mems = GROUPS[group].members
    else:
        print("student not in group", submitter)
        group_mems = [submitter]
    try:
        grade = get_grade(score)[0]
    except IndexError as e:
        print("Got an Index Error?!!")
        print(e)
    for memb in group_mems:
        if memb.id() in GRADES:
            print("Two Submissions?!")
            print(memb.id(), subm.key, subm.compScore)
            print("existing created", GRADES[memb.id()][2], "new", grade.created)
        GRADES[memb.id()] = (grade.score, url, grade.created)


compscores = get_comp_scores()
write(GRADES)


