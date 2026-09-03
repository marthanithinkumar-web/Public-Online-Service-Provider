from flask import Blueprint, jsonify, request

from ..scholarships.catalog import load_catalog

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
