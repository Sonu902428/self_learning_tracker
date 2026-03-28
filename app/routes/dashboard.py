from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Subject, Topic, Subtopic, MockTest

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    subjects = Subject.query.order_by(Subject.created_at.desc()).all()

    total_topics     = Topic.query.count()
    total_subtopics  = Subtopic.query.count()
    completed_topics = sum(1 for s in subjects for t in s.topics if t.is_fully_covered)

    # Overall progress = average of all subject progress
    overall_pct = round(
        sum(s.progress_percent for s in subjects) / len(subjects)
        if subjects else 0
    )

    # Mock stats
    total_mocks    = MockTest.query.filter_by(attempted=True).count()
    avg_mock_score = None
    attempted = MockTest.query.filter_by(attempted=True).all()
    if attempted:
        avg_mock_score = round(sum(m.score for m in attempted) / len(attempted), 1)

    # Recent activity — last 6 topics/subtopics covered
    recent_topics = (Topic.query
                     .filter(Topic.go_through_at.isnot(None))
                     .order_by(Topic.go_through_at.desc())
                     .limit(6).all())

    # Chart data: per-subject progress
    chart_labels = [s.name for s in subjects]
    chart_data   = [s.progress_percent for s in subjects]
    chart_colors = [s.color for s in subjects]

    # Stage breakdown across ALL topics (without subtopics)
    flat_topics = Topic.query.all()
    go_count    = sum(1 for t in flat_topics if t.go_through)
    prac_count  = sum(1 for t in flat_topics if t.practiced)
    mock_count  = sum(1 for t in flat_topics if t.mock_done)

    return render_template('dashboard.html',
        subjects=subjects,
        total_topics=total_topics,
        total_subtopics=total_subtopics,
        completed_topics=completed_topics,
        overall_pct=overall_pct,
        total_mocks=total_mocks,
        avg_mock_score=avg_mock_score,
        recent_topics=recent_topics,
        chart_labels=chart_labels,
        chart_data=chart_data,
        chart_colors=chart_colors,
        go_count=go_count,
        prac_count=prac_count,
        mock_count=mock_count,
    )