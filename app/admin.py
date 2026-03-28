import secrets
from flask import redirect, url_for, request, flash
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms import PasswordField
from wtforms.validators import Optional, Length
from app import db


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login', next=request.url))


class MyAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))
        from app.models import User, Subject, Topic, Subtopic, MockTest
        stats = {
            'users':    User.query.count(),
            'subjects': Subject.query.count(),
            'topics':   Topic.query.count(),
            'subtopics':Subtopic.query.count(),
            'mocks':    MockTest.query.filter_by(attempted=True).count(),
        }
        recent_users  = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_topics = Topic.query.order_by(Topic.created_at.desc()).limit(5).all()
        return self.render('admin/index.html', stats=stats,
                           recent_users=recent_users, recent_topics=recent_topics)


class UserAdmin(SecureModelView):
    column_list           = ('id', 'username', 'email', 'is_admin', 'created_at')
    column_searchable_list = ('username', 'email')
    column_filters        = ('is_admin',)
    column_sortable_list  = ('id', 'username', 'created_at')
    form_excluded_columns = ('password_hash',)
    form_extra_fields = {
        'password': PasswordField('Password',
            validators=[Optional(), Length(min=4, max=100)],
            description='Leave blank when editing to keep existing password.')
    }
    form_columns = ('username', 'email', 'password', 'is_admin')
    can_export   = True
    page_size    = 20

    def on_model_change(self, form, model, is_created):
        pw = form.password.data
        if pw:
            model.set_password(pw)
        elif is_created:
            model.set_password(secrets.token_hex(16))

    def after_model_change(self, form, model, is_created):
        flash(f'User "{model.username}" {"created" if is_created else "updated"}.', 'success')


class SubjectAdmin(SecureModelView):
    column_list           = ('id', 'name', 'color', 'created_at')
    column_searchable_list = ('name',)
    can_export = True


class TopicAdmin(SecureModelView):
    column_list           = ('id', 'name', 'subject', 'go_through', 'practiced', 'mock_done', 'created_at')
    column_searchable_list = ('name',)
    column_filters        = ('go_through', 'practiced', 'mock_done', 'subject')
    can_export = True


class SubtopicAdmin(SecureModelView):
    column_list           = ('id', 'name', 'topic', 'go_through', 'practiced', 'mock_done')
    column_searchable_list = ('name',)
    column_filters        = ('go_through', 'practiced', 'mock_done')
    can_export = True


class MockTestAdmin(SecureModelView):
    column_list = ('id', 'topic', 'subtopic', 'test_number', 'score', 'attempted', 'attempted_at')
    column_filters = ('attempted',)
    can_export = True


def init_admin(app):
    admin = Admin(app, name='LearnTrack Admin', index_view=MyAdminIndex())
    from app.models import User, Subject, Topic, Subtopic, MockTest
    admin.add_view(UserAdmin(User,         db.session, name='Users',     category='Manage'))
    admin.add_view(SubjectAdmin(Subject,   db.session, name='Subjects',  category='Manage'))
    admin.add_view(TopicAdmin(Topic,       db.session, name='Topics',    category='Manage'))
    admin.add_view(SubtopicAdmin(Subtopic, db.session, name='Subtopics', category='Manage'))
    admin.add_view(MockTestAdmin(MockTest, db.session, name='Mock Tests',category='Manage'))
    return admin