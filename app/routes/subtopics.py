import os, uuid
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app, send_from_directory)
from flask_login import login_required
from app import db
from app.models import Topic, Subtopic, MockTest, SubtopicPDF

subtopics_bp = Blueprint('subtopics', __name__, url_prefix='/subtopics')

NUM_MOCK_TESTS = 5


def _init_mock_tests(subtopic_id):
    for i in range(1, NUM_MOCK_TESTS + 1):
        db.session.add(MockTest(subtopic_id=subtopic_id, test_number=i))


def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS'])


@subtopics_bp.route('/add/<int:topic_id>', methods=['GET', 'POST'])
@login_required
def add(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    if request.method == 'POST':
        name  = request.form.get('name','').strip()
        notes = request.form.get('notes','').strip()
        if not name:
            flash('Subtopic name is required.','error')
        else:
            sub = Subtopic(name=name, notes=notes, topic_id=topic_id)
            db.session.add(sub)
            db.session.flush()
            _init_mock_tests(sub.id)
            _handle_pdf_uploads(subtopic_id=sub.id)
            db.session.commit()
            flash(f'Subtopic "{name}" added!','success')
            return redirect(url_for('topics.detail', id=topic_id))
    return render_template('subtopics/form.html', topic=topic, subtopic=None)


@subtopics_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    sub = Subtopic.query.get_or_404(id)
    if request.method == 'POST':
        sub.name  = request.form.get('name','').strip()
        sub.notes = request.form.get('notes','').strip()
        _handle_pdf_uploads(subtopic_id=sub.id)
        db.session.commit()
        flash('Subtopic updated!','success')
        return redirect(url_for('topics.detail', id=sub.topic_id))
    return render_template('subtopics/form.html', topic=sub.topic, subtopic=sub)


@subtopics_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    sub = Subtopic.query.get_or_404(id)
    tid = sub.topic_id
    for pdf in sub.pdfs:
        _delete_pdf_file(pdf.filename)
    db.session.delete(sub)
    db.session.commit()
    flash('Subtopic deleted.','info')
    return redirect(url_for('topics.detail', id=tid))


# ── Progress toggles ──────────────────────────────────────────────────────────

@subtopics_bp.route('/<int:id>/go-through', methods=['POST'])
@login_required
def toggle_go_through(id):
    sub = Subtopic.query.get_or_404(id)
    if not sub.go_through:
        sub.go_through    = True
        sub.go_through_at = datetime.utcnow()
        flash(f'"{sub.name}" marked as Go Through ✅','success')
    else:
        if sub.practiced:
            flash('Cannot undo: Practice already marked.','error')
        else:
            sub.go_through    = False
            sub.go_through_at = None
    db.session.commit()
    return redirect(request.referrer or url_for('topics.detail', id=sub.topic_id))


@subtopics_bp.route('/<int:id>/practice', methods=['POST'])
@login_required
def toggle_practice(id):
    sub = Subtopic.query.get_or_404(id)
    if not sub.go_through:
        flash('Complete "Go Through" first.','error')
    elif not sub.practiced:
        sub.practiced    = True
        sub.practiced_at = datetime.utcnow()
        flash(f'"{sub.name}" marked as Practiced 🏋️','success')
    else:
        if sub.mock_done:
            flash('Cannot undo: Mock already completed.','error')
        else:
            sub.practiced    = False
            sub.practiced_at = None
    db.session.commit()
    return redirect(request.referrer or url_for('topics.detail', id=sub.topic_id))


# ── PDF ───────────────────────────────────────────────────────────────────────

@subtopics_bp.route('/pdf/<int:pdf_id>/delete', methods=['POST'])
@login_required
def delete_pdf(pdf_id):
    pdf = SubtopicPDF.query.get_or_404(pdf_id)
    tid = pdf.subtopic.topic_id
    _delete_pdf_file(pdf.filename)
    db.session.delete(pdf)
    db.session.commit()
    flash('PDF deleted.','info')
    return redirect(request.referrer or url_for('topics.detail', id=tid))


@subtopics_bp.route('/pdf/<int:pdf_id>/view')
@login_required
def view_pdf(pdf_id):
    pdf = SubtopicPDF.query.get_or_404(pdf_id)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], pdf.filename)


def _handle_pdf_uploads(subtopic_id):
    files  = request.files.getlist('pdfs')
    labels = request.form.getlist('pdf_labels')
    for i, file in enumerate(files):
        if file and file.filename and allowed_file(file.filename):
            ext    = file.filename.rsplit('.', 1)[1].lower()
            stored = f"{uuid.uuid4().hex}.{ext}"
            label  = (labels[i].strip() if i < len(labels) and labels[i].strip()
                      else file.filename)
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], stored))
            db.session.add(SubtopicPDF(subtopic_id=subtopic_id, filename=stored, label=label))


def _delete_pdf_file(filename):
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        os.remove(path)