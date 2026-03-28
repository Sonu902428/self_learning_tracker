from app.models import Subject, Topic

def get_subject_count():

    return Subject.query.count()


def get_topic_count():

    return Topic.query.count()


def get_progress():

    topics = Topic.query.all()

    total = len(topics)
    covered = sum(1 for t in topics if t.go_through)

    return {
        "total": total,
        "covered": covered
    }


import sqlite3
def count_topic_in_subject(subject_name):

    subject = Subject.query.filter(
        Subject.name.ilike(f"%{subject_name}%")
    ).first()

    if not subject:
        return 0

    return Topic.query.filter_by(subject_id=subject.id).count()