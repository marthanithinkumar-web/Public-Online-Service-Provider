def test_girl_student_rule_requires_matching_gender(client, monkeypatch):
    from app.routes import scholarships
    monkeypatch.setattr(scholarships, 'load_catalog', lambda *args, **kwargs: {
        'items': [{'id': '1', 'slug': 'pragati', 'title': 'AICTE Pragati Scholarship Scheme for Girl Students', 'eligibility': 'Girl students meeting current criteria.'}]
    })
    missing = client.post('/api/scholarships/pragati/eligibility', json={'answers': {}})
    assert missing.status_code == 200
    assert missing.get_json()['status'] == 'needs_more_information'
    assert 'gender' in missing.get_json()['missing_fields']

    matched = client.post('/api/scholarships/pragati/eligibility', json={'answers': {'gender': 'female'}})
    assert matched.status_code == 200
    assert matched.get_json()['status'] == 'potentially_eligible'
    assert matched.get_json()['official_verification_required'] is True

    failed = client.post('/api/scholarships/pragati/eligibility', json={'answers': {'gender': 'male'}})
    assert failed.get_json()['status'] == 'not_matched'


def test_disability_and_category_rules_are_conservative(client, monkeypatch):
    from app.routes import scholarships
    monkeypatch.setattr(scholarships, 'load_catalog', lambda *args, **kwargs: {
        'items': [{'id': '2', 'slug': 'combo', 'title': 'Scholarship for Students with Disabilities', 'eligibility': 'OBC, EBC and DNT students with disabilities.'}]
    })
    result = client.post('/api/scholarships/combo/eligibility', json={'answers': {'disability': 'yes', 'social_category': 'obc'}})
    assert result.status_code == 200
    body = result.get_json()
    assert body['status'] == 'potentially_eligible'
    assert len(body['checks']) == 2


def test_closed_or_unknown_scholarship_cannot_be_assessed(client, monkeypatch):
    from app.routes import scholarships
    monkeypatch.setattr(scholarships, 'load_catalog', lambda *args, **kwargs: {'items': []})
    response = client.post('/api/scholarships/closed/eligibility', json={'answers': {}})
    assert response.status_code == 404
