import pickle
import app.models
from google.appengine.ext import ndb
from datetime import datetime
import json
import datetime as s
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

def get_ants_id():
    q = app.models.Assignment.query(app.models.Assignment.display_name == "Ants")
    return q.fetch()[0].key.id()

def get_ants_key():
    q = app.models.Assignment.query(app.models.Assignment.display_name == "Ants")
    return q.fetch()[0].key

def get_ants_groups():
    q = app.models.Group.query(app.models.Group.assignment == ndb.Key("Assignment", get_ants_id()))
    return q.fetch()

def parse_email_file():
    emails = open("emails.txt", "rb")
    login_to_email = {}
    for line in emails:
        line = line.decode('utf-8')
        parts = line.strip().split(',')
        login_to_email[parts[-2]] = parts[-1]

    emails.close()

    return login_to_email

def parse_time_file():
    times = open("proj3_times.txt", "rb")
    login_to_time = {}
    for line in times:
        line = line.decode('utf-8')
        parts = line.strip().split(' ')
        login_to_time[parts[-2]] = datetime.strptime(parts[-1], "%m/%d@%H:%M")
    times.close()
    return login_to_time

def get_group_id(email, groups):
    for group in groups:
        if ndb.Key('User', email) in group.members:
            return group.key

def delete_group(main_key):
    main_key.delete()

def get_user_key(email):
    q = app.models.User.query(app.models.User.email == email)
    return q.fetch()[0].key

def make_new_group(emails):
    user_keys = []
    for email in emails:
        one_key = get_user_key(email)
        if one_key:
            user_keys.append(one_key)
        else:
            return False
    p = app.models.Group(assignment=get_ants_key(), members=user_keys)
    key = p.put()
    p2 = key.get()
    return key

def make_final_submission(group_id, submission_key):
    p = app.models.FinalSubmission(assignment=get_ants_key(), group=group_id, submission=submission_key, published=False)
    return p.put()

def get_final_submission(group_id, assign_id, assignment_body, timestamp):
    submissions = []
    group = group_id.get()
    for student in group.members:
        q = app.models.Submission.query(app.models.Submission.submitter == student).filter(app.models.Submission.created >= datetime(2014, 10, 19, 0, 0, 0))
        submissions += get_all_results(q)
    
    submissions = [submission for submission in submissions if submission.assignment.id() == assign_id]
    submissions = [submission for submission in submissions if 'file_contents' in [msg.kind for msg in submission.messages]]
    
    for submission in submissions:
        for message in submission.messages:
            if message.kind == 'file_contents':
                if message.contents['ants.py'] == assignment_body:
                    return submission.key

        if "submit" in submission.tags:
            return submission.key

        if "Submit" in submission.tags:
            return submission.key

    my_messages = [app.models.Message(kind='file_contents', contents={'ants.py': assignment_body}), app.models.Message(kind='analytics', contents={}), app.models.Message(kind='timestamp', contents=str(timestamp)]

    p = app.models.Submission(submitter=group.members[0], assignment=get_ants_key(), messages=my_messages, created=datetime.now())
    return p.put()

def fix_ants():
    assignment_id = get_ants_id()
    submissions = pickle.load(open("submissions.pkl", "rb"))
    login_to_email = parse_email_file()
    login_to_timestamp = parse_time_file()

    ants_groups = get_ants_groups()
    count = 0
    
    for logins in submissions:
        emails = [login_to_email[login] for login in logins]
        group_ids = [get_group_id(email, ants_groups) for email in emails]
        main_id = group_ids[0]
        delete = not main_id
        for iden in group_ids:
            if main_id != iden:
                delete = True
        if delete:
            for iden in group_ids:
                if iden != None:
                    delete_group(iden)
            main_id = make_new_group(emails)
            if not main_id:
                print("This group failed: {0}".format(logins))
                continue

        submission_key = get_final_submission(main_id, get_ants_key(), submissions[logins], min([login_to_timestamp[login] for login in logins]))

        if make_final_submission(submission_key, main_id):
            count += 1
            print("Successfully processed {0} out of {1}".format(count, len(submissions)))
