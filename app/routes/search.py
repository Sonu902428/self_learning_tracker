from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required
from app.models import Subject, Topic, Subtopic, TopicPDF

search_bp = Blueprint('search', __name__, url_prefix='/search')


@search_bp.route('/')
@login_required
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return render_template('search/results.html', q='', results=[])

    like = f'%{q}%'

    subjects  = Subject.query.filter(Subject.name.ilike(like)).all()
    topics    = Topic.query.filter(Topic.name.ilike(like)).all()
    subtopics = Subtopic.query.filter(Subtopic.name.ilike(like)).all()
    topicspdf = TopicPDF.query.filter(TopicPDF.label.ilike(like)).all()

    

    results = []
    for s in subjects:
        results.append({'type': 'Subject', 'name': s.name,
                        'url': f'/subjects/{s.id}', 'parent': None,
                        'color': s.color})
    for t in topics:
        results.append({'type': 'Topic', 'name': t.name,
                        'url': f'/topics/{t.id}',
                        'parent': t.subject.name,
                        'color': t.subject.color})
    for s in subtopics:
        results.append({'type': 'Subtopic', 'name': s.name,
                        'url': f'/topics/{s.topic_id}',
                        'parent': f'{s.topic.subject.name} → {s.topic.name}',
                        'color': s.topic.subject.color})
        
    for tp in topicspdf:
        results.append({'type': 'TopicPDF', 'name':tp.label,
                        'url': url_for('topics.view_pdf', pdf_id=tp.id),
                        'parent': f'{tp.topic.name}',
                        'color': tp.topic.subject.color})


    return render_template('search/results.html', q=q, results=results)


@search_bp.route('/ajax')
@login_required
def ajax_search():
    """Returns JSON for live search dropdown."""
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    like = f'%{q}%'
    results = []

    for s in Subject.query.filter(Subject.name.ilike(like)).limit(3).all():
        results.append({'type': 'Subject', 'name': s.name,
                        'url': f'/subjects/{s.id}', 'parent': ''})
    for t in Topic.query.filter(Topic.name.ilike(like)).limit(5).all():
        results.append({'type': 'Topic', 'name': t.name,
                        'url': f'/topics/{t.id}',
                        'parent': t.subject.name})
    for s in Subtopic.query.filter(Subtopic.name.ilike(like)).limit(5).all():
        results.append({'type': 'Subtopic', 'name': s.name,
                        'url': f'/topics/{s.topic_id}',
                        'parent': f'{s.topic.name}'})

    return jsonify(results[:10])