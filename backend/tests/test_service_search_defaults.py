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


def test_default_services_include_editable_thirty_rupee_railway_booking(client):
    response = client.get('/api/services/search?q=railway ticket')

    assert response.status_code == 200
    services = response.get_json()
    railway = next(service for service in services if service['name'] == 'Railway Ticket Booking Assistance')
    assert railway['price_inr'] == 30.0
    assert railway['category'] == 'Travel & Ticketing Assistance'
    assert 'OTP' in railway['description']
    detail = client.get(f"/api/services/{railway['id']}").get_json()
    field_keys = {field['key'] for field in detail['requirements']['fields']}
    assert {'journey_from', 'journey_to', 'journey_date', 'passengers'} <= field_keys
    assert 'OTP' in detail['requirements']['safety_note']


def test_catalog_summary_is_cacheable_and_omits_form_definitions(client):
    response = client.get('/api/services')
    assert response.status_code == 200
    assert 'max-age=60' in response.headers['Cache-Control']
    assert response.get_json()
    assert all('requirements' not in service for service in response.get_json())
    assert all(service.get('slug') for service in response.get_json())


def test_public_service_detail_has_stable_descriptive_slug_route(client):
    catalog = client.get('/api/services').get_json()
    service = next(item for item in catalog if item['name'] == 'Government Job Application')

    response = client.get(f"/api/services/by-slug/{service['slug']}")

    assert response.status_code == 200
    assert response.get_json()['id'] == service['id']
    assert response.get_json()['slug'] == 'government-job-application'
    assert 'max-age=300' in response.headers['Cache-Control']


def test_document_pdf_service_is_searchable_five_rupees_and_has_document_options(client):
    response = client.get('/api/services/search?q=apaar pdf')
    assert response.status_code == 200
    service = next(item for item in response.get_json() if item['name'] == 'Official Document PDF Access Assistance')
    assert service['price_inr'] == 5.0
    assert service['is_active'] is True

    detail = client.get(f"/api/services/{service['id']}")
    assert detail.status_code == 200
    data = detail.get_json()
    document_field = next(field for field in data['requirements']['fields'] if field['key'] == 'document_type')
    assert {'Aadhaar / e-Aadhaar', 'Voter ID / e-EPIC', 'PAN / e-PAN', 'ABHA Health ID', 'APAAR ID'} <= set(document_field['options'])
    assert 'do not create or alter official documents' in data['requirements']['safety_note'].lower()


def test_service_search_matches_partial_words_categories_and_keywords(client):
    from app.models.service import Category, Service
    from app.utils.database import db

    with client.application.app_context():
        category = Category(name='Citizen Identity Services')
        db.session.add(category)
        db.session.flush()
        db.session.add(Service(
            name='Identity Document Assistance',
            description='Guidance for a citizen identity request.',
            keywords='identity verification document',
            category_id=category.id,
            is_active=True,
        ))
        db.session.commit()

    partial = client.get('/api/services/search?q=docum')
    category = client.get('/api/services/search?q=CiTiZeN')
    keyword = client.get('/api/services/search?q=verificat')

    assert partial.status_code == 200
    assert category.status_code == 200
    assert keyword.status_code == 200
    assert any(service['name'] == 'Identity Document Assistance' for service in partial.get_json())
    assert any(service['name'] == 'Identity Document Assistance' for service in category.get_json())
    assert any(service['name'] == 'Identity Document Assistance' for service in keyword.get_json())
