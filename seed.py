"""Run once: python seed.py   →  Login: admin / admin123"""
from app import create_app, db
from app.models import User, Subject, Topic, Subtopic, MockTest
import os

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")


app = create_app()

with app.app_context():
    if not User.query.filter_by(username=ADMIN_USER).first():
        u = User(username=ADMIN_USER, email=ADMIN_EMAIL, is_admin=True)
        u.set_password(ADMIN_PASS)
        db.session.add(u)
        print(f"✅ Admin: {ADMIN_USER}")

    if Subject.query.count() == 0:
        data = [
            {
                'name':'Python Basics','color':'#00d4ff',
                'description':'Core Python for beginners',
                'topics':[
                    {'name':'Functions','subtopics':['Parameters','Return Statements','Lambda']},
                    {'name':'OOP Concepts','subtopics':['Classes','Inheritance','Polymorphism']},
                    {'name':'List Comprehension','subtopics':[]},
                ]
            },
            {
                'name':'Data Structures','color':'#8b5cf6',
                'description':'DSA fundamentals',
                'topics':[
                    {'name':'Arrays & Lists','subtopics':[]},
                    {'name':'Trees','subtopics':['Binary Tree','BST','AVL Tree']},
                ]
            },
        ]
        for sd in data:
            s = Subject(name=sd['name'], color=sd['color'], description=sd['description'])
            db.session.add(s); db.session.flush()
            for td in sd['topics']:
                t = Topic(name=td['name'], subject_id=s.id)
                db.session.add(t); db.session.flush()
                # Add 5 mock tests per topic (if no subtopics)
                if not td['subtopics']:
                    for i in range(1, 6):
                        db.session.add(MockTest(topic_id=t.id, test_number=i))
                for sname in td['subtopics']:
                    sub = Subtopic(name=sname, topic_id=t.id)
                    db.session.add(sub); db.session.flush()
                    for i in range(1, 6):
                        db.session.add(MockTest(subtopic_id=sub.id, test_number=i))
        print("✅ Sample data added")

    db.session.commit()
    print("\n🚀 Run:  python run.py  →  http://127.0.0.1:5000")