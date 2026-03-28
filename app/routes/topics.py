import os, uuid
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app, send_from_directory)
from flask_login import login_required
from app import db
from app.models import Subject, Topic, MockTest, TopicPDF

topics_bp = Blueprint('topics', __name__, url_prefix='/topics')

NUM_MOCK_TESTS = 5


def _init_mock_tests(topic_id):
    """Create 5 blank mock test slots for a topic."""
    for i in range(1, NUM_MOCK_TESTS + 1):
        db.session.add(MockTest(topic_id=topic_id, test_number=i))


def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS'])


# ── CRUD ──────────────────────────────────────────────────────────────────────

@topics_bp.route('/add/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def add(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'POST':
        name  = request.form.get('name','').strip()
        notes = request.form.get('notes','').strip()
        if not name:
            flash('Topic name is required.','error')
        else:
            topic = Topic(name=name, notes=notes, subject_id=subject_id)
            db.session.add(topic)
            db.session.flush()
            _init_mock_tests(topic.id)
            uploaded, errors = _handle_pdf_uploads(topic_id=topic.id)
            db.session.commit()
            flash(f'Topic "{name}" added!','success')
            if uploaded > 0:
                flash(f'{uploaded} PDF(s) uploaded.','info')
            if errors:
                flash(f'Failed to upload: {", ".join(errors)}','warning')
            return redirect(url_for('subjects.detail', id=subject_id))
    return render_template('topics/form.html', subject=subject, topic=None)


@topics_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    topic = Topic.query.get_or_404(id)
    if request.method == 'POST':
        topic.name  = request.form.get('name','').strip()
        topic.notes = request.form.get('notes','').strip()
        uploaded, errors = _handle_pdf_uploads(topic_id=topic.id)
        db.session.commit()
        flash('Topic updated!','success')
        if uploaded > 0:
            flash(f'{uploaded} PDF(s) uploaded.','info')
        if errors:
            flash(f'Failed to upload: {", ".join(errors)}','warning')
        return redirect(url_for('subjects.detail', id=topic.subject_id))
    return render_template('topics/form.html', subject=topic.subject, topic=topic)


@topics_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    topic = Topic.query.get_or_404(id)
    sid   = topic.subject_id
    for pdf in topic.pdfs:
        _delete_pdf_file(pdf.filename)
    db.session.delete(topic)
    db.session.commit()
    flash('Topic deleted.','info')
    return redirect(url_for('subjects.detail', id=sid))


@topics_bp.route('/<int:id>')
@login_required
def detail(id):
    topic = Topic.query.get_or_404(id)
    # Only direct mock tests (subtopic_id IS NULL)
    mock_tests = MockTest.query.filter_by(topic_id=id, subtopic_id=None)\
                               .order_by(MockTest.test_number).all()
    return render_template('topics/detail.html', topic=topic, mock_tests=mock_tests)


# ── Progress stage toggles ────────────────────────────────────────────────────

@topics_bp.route('/<int:id>/go-through', methods=['POST'])
@login_required
def toggle_go_through(id):
    topic = Topic.query.get_or_404(id)
    if not topic.go_through:
        topic.go_through    = True
        topic.go_through_at = datetime.utcnow()
        flash(f'"{topic.name}" marked as Go Through ✅','success')
    else:
        # Undo — only if practiced not done yet
        if topic.practiced:
            flash('Cannot undo: Practice already marked.','error')
        else:
            topic.go_through    = False
            topic.go_through_at = None
    db.session.commit()
    return redirect(request.referrer or url_for('topics.detail', id=id))


@topics_bp.route('/<int:id>/practice', methods=['POST'])
@login_required
def toggle_practice(id):
    topic = Topic.query.get_or_404(id)
    if not topic.go_through:
        flash('Complete "Go Through" first before marking Practice.','error')
    elif not topic.practiced:
        topic.practiced    = True
        topic.practiced_at = datetime.utcnow()
        flash(f'"{topic.name}" marked as Practiced 🏋️','success')
    else:
        if topic.mock_done:
            flash('Cannot undo: Mock already completed.','error')
        else:
            topic.practiced    = False
            topic.practiced_at = None
    db.session.commit()
    return redirect(request.referrer or url_for('topics.detail', id=id))


# ── PDF ───────────────────────────────────────────────────────────────────────

@topics_bp.route('/pdf/<int:pdf_id>/delete', methods=['POST'])
@login_required
def delete_pdf(pdf_id):
    pdf = TopicPDF.query.get_or_404(pdf_id)
    sid = pdf.topic.subject_id
    _delete_pdf_file(pdf.filename)
    db.session.delete(pdf)
    db.session.commit()
    flash('PDF deleted.','info')
    return redirect(request.referrer or url_for('subjects.detail', id=sid))


@topics_bp.route('/pdf/<int:pdf_id>/view')
@login_required
def view_pdf(pdf_id):
    pdf = TopicPDF.query.get_or_404(pdf_id)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], pdf.filename)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _handle_pdf_uploads(topic_id):
    """Handle PDF file uploads for a topic. Returns tuple (uploaded_count, error_list)"""
    files = request.files.getlist('pdfs[]')
    labels = request.form.getlist('pdf_labels[]')
    
    uploaded_count = 0
    error_files = []

    for i, file in enumerate(files):
        # Skip empty file inputs
        if not file or not file.filename:
            continue

        if not allowed_file(file.filename):
            error_files.append(file.filename)
            continue

        try:
            ext = file.filename.rsplit('.', 1)[1].lower()
            stored = f"{uuid.uuid4().hex}.{ext}"

            label = file.filename
            if i < len(labels) and labels[i].strip():
                label = labels[i].strip()

            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], stored)
            file.save(filepath)

            pdf = TopicPDF(
                topic_id=topic_id,
                filename=stored,
                label=label
            )

            db.session.add(pdf)
            uploaded_count += 1
            
        except Exception as e:
            current_app.logger.error(f"PDF upload error for {file.filename}: {str(e)}")
            error_files.append(file.filename)

    return (uploaded_count, error_files)


def _delete_pdf_file(filename):
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(path):
        os.remove(path)


@topics_bp.route("/topic_list")
def topic_list():
    data = Topic.query.all()
    # print(data.name)
    return render_template('topics/topic_list.html', data = data)