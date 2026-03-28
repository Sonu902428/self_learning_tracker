from datetime import datetime
from flask import Blueprint, redirect, url_for, flash, request, render_template, jsonify
from flask_login import login_required
from app import db
from app.models import Topic, Subtopic, MockTest

mocks_bp = Blueprint('mocks', __name__, url_prefix='/mocks')

PASS_THRESHOLD  = 80.0   # average must be >= 80 to pass
NUM_MOCK_TESTS  = 5


def _evaluate_and_update(obj, tests):
    """
    After all 5 tests attempted:
    - avg >= 80 → mock_done = True
    - avg < 80  → reset all tests, user must retry
    Returns (passed: bool, avg: float)
    """
    attempted = [t for t in tests if t.attempted]
    if len(attempted) < NUM_MOCK_TESTS:
        return None, None   # not all done yet

    avg = sum(t.score for t in attempted) / len(attempted)

    if avg >= PASS_THRESHOLD:
        obj.mock_done    = True
        obj.mock_done_at = datetime.utcnow()
        db.session.commit()
        return True, round(avg, 1)
    else:
        # Reset all mock tests
        for t in tests:
            t.score      = None
            t.attempted  = False
            t.attempted_at = None
        obj.mock_done    = False
        obj.mock_done_at = None
        db.session.commit()
        return False, round(avg, 1)


# ── Submit score for a topic's mock test ─────────────────────────────────────

@mocks_bp.route('/topic/<int:topic_id>/submit', methods=['POST'])
@login_required
def submit_topic_mock(topic_id):
    topic = Topic.query.get_or_404(topic_id)

    if not topic.can_attempt_mock:
        flash('You must complete Practice before attempting mock tests.', 'error')
        return redirect(url_for('topics.detail', id=topic_id))

    test_id = request.form.get('test_id', type=int)
    score   = request.form.get('score',   type=float)

    if score is None or not (0 <= score <= 100):
        flash('Score must be between 0 and 100.', 'error')
        return redirect(url_for('topics.detail', id=topic_id))

    test = MockTest.query.get_or_404(test_id)
    test.score       = score
    test.attempted   = True
    test.attempted_at = datetime.utcnow()
    db.session.commit()

    # Check if all 5 done
    all_tests = MockTest.query.filter_by(topic_id=topic_id, subtopic_id=None)\
                              .order_by(MockTest.test_number).all()
    passed, avg = _evaluate_and_update(topic, all_tests)

    if passed is True:
        flash(f'🎉 All tests done! Average: {avg}% — Mock PASSED! Topic fully covered.', 'success')
    elif passed is False:
        flash(f'❌ Average score: {avg}% (need ≥ 80%). All tests reset — please retry.', 'error')
    else:
        remaining = sum(1 for t in all_tests if not t.attempted)
        flash(f'Test #{test.test_number} saved: {score:.0f}%. {remaining} test(s) remaining.', 'info')

    return redirect(url_for('topics.detail', id=topic_id))


# ── Submit score for a subtopic's mock test ───────────────────────────────────

@mocks_bp.route('/subtopic/<int:subtopic_id>/submit', methods=['POST'])
@login_required
def submit_subtopic_mock(subtopic_id):
    sub = Subtopic.query.get_or_404(subtopic_id)

    if not sub.can_attempt_mock:
        flash('Complete Practice first before attempting mock tests.', 'error')
        return redirect(url_for('topics.detail', id=sub.topic_id))

    test_id = request.form.get('test_id', type=int)
    score   = request.form.get('score',   type=float)

    if score is None or not (0 <= score <= 100):
        flash('Score must be between 0 and 100.', 'error')
        return redirect(url_for('topics.detail', id=sub.topic_id))

    test = MockTest.query.get_or_404(test_id)
    test.score        = score
    test.attempted    = True
    test.attempted_at = datetime.utcnow()
    db.session.commit()

    all_tests = MockTest.query.filter_by(subtopic_id=subtopic_id)\
                              .order_by(MockTest.test_number).all()
    passed, avg = _evaluate_and_update(sub, all_tests)

    if passed is True:
        flash(f'🎉 All tests done! Average: {avg}% — Mock PASSED!', 'success')
    elif passed is False:
        flash(f'❌ Average: {avg}% (need ≥ 80%). Tests reset — please retry.', 'error')
    else:
        remaining = sum(1 for t in all_tests if not t.attempted)
        flash(f'Test #{test.test_number} saved: {score:.0f}%. {remaining} remaining.', 'info')

    return redirect(url_for('topics.detail', id=sub.topic_id))


# ── Reset all mock tests manually ────────────────────────────────────────────

@mocks_bp.route('/topic/<int:topic_id>/reset', methods=['POST'])
@login_required
def reset_topic_mocks(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    tests = MockTest.query.filter_by(topic_id=topic_id, subtopic_id=None).all()
    for t in tests:
        t.score = None; t.attempted = False; t.attempted_at = None
    topic.mock_done = False; topic.mock_done_at = None
    db.session.commit()
    flash('Mock tests reset.', 'info')
    return redirect(url_for('topics.detail', id=topic_id))


@mocks_bp.route('/subtopic/<int:subtopic_id>/reset', methods=['POST'])
@login_required
def reset_subtopic_mocks(subtopic_id):
    sub   = Subtopic.query.get_or_404(subtopic_id)
    tests = MockTest.query.filter_by(subtopic_id=subtopic_id).all()
    for t in tests:
        t.score = None; t.attempted = False; t.attempted_at = None
    sub.mock_done = False; sub.mock_done_at = None
    db.session.commit()
    flash('Mock tests reset.', 'info')
    return redirect(url_for('topics.detail', id=sub.topic_id))