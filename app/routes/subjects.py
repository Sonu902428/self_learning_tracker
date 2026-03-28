from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.models import Subject

subjects_bp = Blueprint('subjects', __name__, url_prefix='/subjects')


@subjects_bp.route('/')
@login_required
def index():
    subjects = Subject.query.order_by(Subject.created_at.desc()).all()
    return render_template('subjects/index.html', subjects=subjects)


@subjects_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name  = request.form.get('name','').strip()
        desc  = request.form.get('description','').strip()
        color = request.form.get('color','#00d4ff')
    
        if not name:
            flash('Subject name is required.','error')
        elif Subject.query.filter_by(name=name).first():
            flash('Subject already exists.','error')
        else:
            db.session.add(Subject(name=name, description=desc, color=color))
            db.session.commit()
            flash(f'Subject "{name}" created!','success')
            return redirect(url_for('subjects.index'))
    return render_template('subjects/form.html', subject=None)


@subjects_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    subject = Subject.query.get_or_404(id)
    if request.method == 'POST':
        subject.name        = request.form.get('name','').strip()
        subject.description = request.form.get('description','').strip()
        subject.color       = request.form.get('color','#00d4ff')
        db.session.commit()
        flash('Subject updated!','success')
        return redirect(url_for('subjects.index'))
    return render_template('subjects/form.html', subject=subject)


@subjects_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    flash(f'Subject "{subject.name}" deleted.','info')
    return redirect(url_for('subjects.index'))


@subjects_bp.route('/<int:id>')
@login_required
def detail(id):
    subject = Subject.query.get_or_404(id)
    return render_template('subjects/detail.html', subject=subject)