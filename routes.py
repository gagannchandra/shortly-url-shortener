from flask import Blueprint, abort, jsonify, redirect, render_template, request
from urllib.parse import urlparse

from models import URLMap, db
from utils import generate_short_code

bp = Blueprint('main', __name__)


# ── API ──────────────────────────────────────────────────────────────────────

@bp.route('/api/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    if not data or 'long_url' not in data:
        return jsonify({'error': 'long_url is a required field.'}), 400

    long_url = data['long_url']
    parsed = urlparse(long_url)
    if not parsed.scheme:
        long_url = 'https://' + long_url
    elif parsed.scheme not in ('http', 'https'):
        return jsonify({'error': 'URL must start with http:// or https://'}), 400

    custom_alias = data.get('custom_alias')

    if custom_alias:
        if not custom_alias.isalnum():
            return jsonify({'error': 'Custom alias can only contain letters and numbers.'}), 400
        if not (4 <= len(custom_alias) <= 30):
            return jsonify({'error': 'Custom alias must be between 4 and 30 characters long.'}), 400
        if URLMap.query.filter_by(short_code=custom_alias).first():
            return jsonify({'error': 'This custom alias is already in use. Please choose another.'}), 409
        short_code = custom_alias
    else:
        while True:
            code = generate_short_code()
            if not URLMap.query.filter_by(short_code=code).first():
                short_code = code
                break

    new_entry = URLMap(long_url=long_url, short_code=short_code)
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({'short_url': f"{request.host_url}{short_code}"}), 201


# ── Pages ─────────────────────────────────────────────────────────────────────

@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/analytics/<string:short_code>')
def show_analytics(short_code):
    entry = URLMap.query.filter_by(short_code=short_code).first()
    if not entry:
        abort(404)
    return render_template('analytics.html', url_data=entry)


@bp.route('/<string:short_code>')
def redirect_to_long_url(short_code):
    entry = URLMap.query.filter_by(short_code=short_code).first()
    if not entry:
        abort(404)
    entry.clicks += 1
    db.session.commit()
    return redirect(entry.long_url)
