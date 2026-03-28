from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# ─────────────────────────────────────────────────────────────────────────────
#  USER
# ─────────────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    is_admin      = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ─────────────────────────────────────────────────────────────────────────────
#  SUBJECT
# ─────────────────────────────────────────────────────────────────────────────
class Subject(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color       = db.Column(db.String(7), default='#00d4ff')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    topics = db.relationship('Topic', backref='subject', lazy=True,
                             cascade='all, delete-orphan',
                             order_by='Topic.order')

    # ── Computed ──────────────────────────────────────────────────────────────
    @property
    def total_topics(self):
        return len(self.topics)

    @property
    def completed_topics(self):
        return sum(1 for t in self.topics if t.is_fully_covered)

    @property
    def progress_percent(self):
        """Average progress across all topics."""
        if not self.topics:
            return 0
        return round(sum(t.progress_percent for t in self.topics) / len(self.topics))

    def __repr__(self):
        return f'<Subject {self.name}>'


# ─────────────────────────────────────────────────────────────────────────────
#  TOPIC
# ─────────────────────────────────────────────────────────────────────────────
class Topic(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    name       = db.Column(db.String(200), nullable=False)
    notes      = db.Column(db.Text)
    order      = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Progress flags ────────────────────────────────────────────────────────
    go_through    = db.Column(db.Boolean, default=False)
    practiced     = db.Column(db.Boolean, default=False)
    mock_done     = db.Column(db.Boolean, default=False)

    go_through_at = db.Column(db.DateTime, nullable=True)
    practiced_at  = db.Column(db.DateTime, nullable=True)
    mock_done_at  = db.Column(db.DateTime, nullable=True)

    # ── Relations ─────────────────────────────────────────────────────────────
    subtopics  = db.relationship('Subtopic', backref='topic', lazy=True,
                                 cascade='all, delete-orphan',
                                 order_by='Subtopic.order')
    mock_tests = db.relationship('MockTest', backref='topic', lazy=True,
                                 cascade='all, delete-orphan',
                                 primaryjoin="and_(MockTest.topic_id==Topic.id, MockTest.subtopic_id==None)",
                                 foreign_keys='MockTest.topic_id')
    pdfs       = db.relationship('TopicPDF', backref='topic', lazy=True,
                                 cascade='all, delete-orphan')

    # ── Progress logic ────────────────────────────────────────────────────────
    @property
    def has_subtopics(self):
        return len(self.subtopics) > 0

    @property
    def progress_percent(self):
        """
        If topic has subtopics → average of subtopic progress.
        Else → own flags: go_through=25, practiced=40, mock_done=35
        """
        if self.has_subtopics:
            if not self.subtopics:
                return 0
            return round(sum(s.progress_percent for s in self.subtopics) / len(self.subtopics))
        return (self.go_through * 25) + (self.practiced * 40) + (self.mock_done * 35)

    @property
    def is_fully_covered(self):
        if self.has_subtopics:
            return all(s.is_fully_covered for s in self.subtopics)
        return self.go_through and self.practiced and self.mock_done

    @property
    def average_mock_score(self):
        tests = [t for t in self.mock_tests if t.attempted]
        if not tests:
            return None
        return round(sum(t.score for t in tests) / len(tests), 1)

    @property
    def confidence_level(self):
        avg = self.average_mock_score
        if avg is None:
            return None
        if avg < 40:   return ('Weak',    'weak')
        if avg < 60:   return ('Low',     'low')
        if avg < 75:   return ('Medium',  'medium')
        if avg < 90:   return ('Strong',  'strong')
        return             ('Mastered', 'mastered')

    @property
    def mock_tests_attempted(self):
        return sum(1 for t in self.mock_tests if t.attempted)

    @property
    def can_attempt_mock(self):
        return self.practiced

    def __repr__(self):
        return f'<Topic {self.name}>'


# ─────────────────────────────────────────────────────────────────────────────
#  SUBTOPIC
# ─────────────────────────────────────────────────────────────────────────────
class Subtopic(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    name     = db.Column(db.String(200), nullable=False)
    notes    = db.Column(db.Text)
    order    = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Progress flags ────────────────────────────────────────────────────────
    go_through    = db.Column(db.Boolean, default=False)
    practiced     = db.Column(db.Boolean, default=False)
    mock_done     = db.Column(db.Boolean, default=False)

    go_through_at = db.Column(db.DateTime, nullable=True)
    practiced_at  = db.Column(db.DateTime, nullable=True)
    mock_done_at  = db.Column(db.DateTime, nullable=True)

    mock_tests = db.relationship('MockTest', backref='subtopic', lazy=True,
                                 cascade='all, delete-orphan',
                                 foreign_keys='MockTest.subtopic_id')
    pdfs       = db.relationship('SubtopicPDF', backref='subtopic', lazy=True,
                                 cascade='all, delete-orphan')

    @property
    def progress_percent(self):
        return (self.go_through * 25) + (self.practiced * 40) + (self.mock_done * 35)

    @property
    def is_fully_covered(self):
        return self.go_through and self.practiced and self.mock_done

    @property
    def average_mock_score(self):
        tests = [t for t in self.mock_tests if t.attempted]
        if not tests:
            return None
        return round(sum(t.score for t in tests) / len(tests), 1)

    @property
    def confidence_level(self):
        avg = self.average_mock_score
        if avg is None:
            return None
        if avg < 40:   return ('Weak',    'weak')
        if avg < 60:   return ('Low',     'low')
        if avg < 75:   return ('Medium',  'medium')
        if avg < 90:   return ('Strong',  'strong')
        return             ('Mastered', 'mastered')

    @property
    def can_attempt_mock(self):
        return self.practiced

    def __repr__(self):
        return f'<Subtopic {self.name}>'


# ─────────────────────────────────────────────────────────────────────────────
#  MOCK TEST  (shared for Topic and Subtopic)
# ─────────────────────────────────────────────────────────────────────────────
class MockTest(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    topic_id    = db.Column(db.Integer, db.ForeignKey('topic.id'),    nullable=True)
    subtopic_id = db.Column(db.Integer, db.ForeignKey('subtopic.id'), nullable=True)
    test_number = db.Column(db.Integer, nullable=False)   # 1–5
    score       = db.Column(db.Float,   nullable=True)    # 0–100
    attempted   = db.Column(db.Boolean, default=False)
    attempted_at = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        parent = f'T{self.topic_id}' if self.topic_id else f'S{self.subtopic_id}'
        return f'<MockTest {parent} #{self.test_number} score={self.score}>'


# ─────────────────────────────────────────────────────────────────────────────
#  PDF ATTACHMENTS
# ─────────────────────────────────────────────────────────────────────────────
class TopicPDF(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    topic_id    = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    filename    = db.Column(db.String(255), nullable=False)
    label       = db.Column(db.String(200))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class SubtopicPDF(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    subtopic_id  = db.Column(db.Integer, db.ForeignKey('subtopic.id'), nullable=False)
    filename     = db.Column(db.String(255), nullable=False)
    label        = db.Column(db.String(200))
    uploaded_at  = db.Column(db.DateTime, default=datetime.utcnow)