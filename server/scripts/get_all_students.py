import pickle
import argparse
import app.models
from google.appengine.ext import ndb
from datetime import datetime

ASSIGN_NAME = 'Ants'
STUDENTS = []
GROUPS = []
DUE_DATE = datetime(2014, 10, 24, 1, 0, 0, 0)

def to_datetime(string):
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S.%f")

def get_all_results(q):
    print("Running query " + str(q))
    results, cursor, more = q.fetch_page(1000)
    all_results = results[:]
    while more:
        print("Fetched {0} results".format(len(all_results)))
        results, cursor, more = q.fetch_page(1000, start_cursor=cursor)
        all_results += results
    print("Fetched {0} results".format(len(all_results)))
    return all_results


def get_assignment_id(name):
    q = app.models.Assignment.query(app.models.Assignment.display_name == name)
    return q.fetch()[0].key.id()

def get_groups(assign_id):
    q = app.models.Group.query(app.models.Group.assignment == ndb.Key('Assignment', assign_id))
    return q.fetch()

def get_students():
    q = app.models.User.query(app.models.User.role == 'student')
    student_records = get_all_results(q)
    return [str(record.email) for record in student_records]

def get_final_submission(group, assign_id):
    submissions = []
    for student in group:
        q = app.models.Submission.query(app.models.Submission.submitter == ndb.Key('User', student)).filter(app.models.Submission.created >= datetime(2014, 10, 19, 0, 0, 0))
        submissions += get_all_results(q)

    submissions = [submission for submission in submissions if submission.assignment.id() == assign_id]
    submissions = [submission for submission in submissions if 'file_contents' in [msg.kind for msg in submission.messages]]
    if not submissions:
        return None, None

    latest_submission = submissions[0]
    if latest_submission.db_created == None:
        latest_timestamp = latest_submission.created
    else:
        latest_timestamp = min(latest_submission.created, latest_submission.db_created)

    for submission in submissions:
        if submission.db_created == None:
            current_timestamp = submission.created
        else:
            current_timestamp = min(submission.created, submission.db_created)
        if current_timestamp <= DUE_DATE and current_timestamp > latest_timestamp:
            latest_submission = submission
            latest_timestamp = current_timestamp

        if "Submit" in submission.tags or "submit" in submission.tags:
            return submission.submitter.id(), submission

    return latest_submission.submitter.id(), latest_submission

def get_file_and_time(submission):
    if submission.db_created == None:
        timestamp = submission.created
    else:
        timestamp = min(submission.created, submission.db_created)
    for message in submission.messages:
        if message.kind == 'file_contents':
            return message.contents, timestamp, submission.key.id()

def get_results():
    try:
        assign_id = get_assignment_id(ASSIGN_NAME)
        groups = GROUPS if STUDENTS else get_groups(assign_id)
        all_students = STUDENTS if STUDENTS else get_students()
        with open("ants_submissions.pkl", "rb") as f:
            student_to_submission = pickle.load(f)
        initial = len(all_students)
        completed = 0

        for group in groups:
            student_tup = tuple(member.id() for member in group.members)
            if student_tup not in student_to_submission:
                submitter, submission = get_final_submission(student_tup, assign_id)
                if submitter != None:
                    student_to_submission[student_tup] = get_file_and_time(submission), submitter
                else:
                    student_to_submission[student_tup] = None, None

            for student in student_tup:
                if student in all_students:
                    all_students.remove(student)
                completed += 1
                print("{0} out of {1} left".format(initial - completed, initial))

        for student in all_students:
            if (student,) not in student_to_submission:
                submitter, submission = get_final_submission([student], assign_id)
                if submitter != None:
                    student_to_submission[(submitter,)] = get_file_and_time(submission), submitter
                else:
                    student_to_submission[(submitter,)] = None, None

            completed += 1
            print("{0} out of {1} left".format(initial - completed, initial))

    finally:
        pickle.dump(student_to_submission, open("ants_submissions.pkl", "wb"))

get_results()
