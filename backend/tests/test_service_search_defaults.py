def test_default_services_are_searchable(client):
    response = client.get('/api/services/search?q=job')

    assert response.status_code == 200
    services = response.get_json()
    assert any('job' in (service.get('name', '') + ' ' + service.get('keywords', '')).lower() for service in services)


def test_default_services_include_public_categories(client):
    response = client.get('/api/services')

    assert response.status_code == 200
    services = response.get_json()
    categories = {service.get('category') for service in services}
    assert 'Certificates' in categories
    assert 'Government Jobs' in categories
    assert 'Scholarships' in categories
    assert 'MeeSeva / Public Services' in categories
