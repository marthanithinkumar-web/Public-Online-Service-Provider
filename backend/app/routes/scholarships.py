from flask import Blueprint, jsonify, request

from ..scholarships.catalog import load_catalog
from ..scholarships.eligibility import assess_scholarship

bp = Blueprint('scholarships', __name__)


@bp.get('/')
def list_scholarships():
    payload = load_catalog(request.args.get('q', '').strip())
    response = jsonify(payload)
    response.headers['Cache-Control'] = 'public, max-age=120, stale-while-revalidate=600'
    return response


@bp.get('/<string:slug>')
def scholarship_detail(slug):
    payload = load_catalog()
    item = next((entry for entry in payload['items'] if entry.get('slug') == slug), None)
    if not item:
        return jsonify({'error': 'Scholarship is unavailable or applications have closed.'}), 404
    response = jsonify(item)
    response.headers['Cache-Control'] = 'public, max-age=120, stale-while-revalidate=600'
    return response


@bp.post('/<string:slug>/eligibility')
def scholarship_eligibility(slug):
    payload = load_catalog()
    item = next((entry for entry in payload['items'] if entry.get('slug') == slug), None)
    if not item:
        return jsonify({'error': 'Scholarship is unavailable or applications have closed.'}), 404
    data = request.get_json(silent=True) or {}
    answers = data.get('answers') or {}
    if not isinstance(answers, dict):
        return jsonify({'error': 'Eligibility answers must use named fields.'}), 400
    return jsonify({'scholarship': {'id': item.get('id'), 'slug': item.get('slug'), 'title': item.get('title')}, **assess_scholarship(item, answers)})
