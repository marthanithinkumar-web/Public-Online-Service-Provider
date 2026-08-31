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
    railway = next(service for service in services if service['name'] == 'Railway Ticket Booking Apply')
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
    service = next(item for item in response.get_json() if item['name'] == 'Official Document PDF Access Apply')
    assert service['price_inr'] == 5.0
    assert service['is_active'] is True

    detail = client.get(f"/api/services/{service['id']}")
    assert detail.status_code == 200
    data = detail.get_json()
    document_field = next(field for field in data['requirements']['fields'] if field['key'] == 'document_type')
    assert {'Aadhaar / e-Aadhaar', 'Voter ID / e-EPIC', 'PAN / e-PAN', 'ABHA Health ID', 'APAAR ID'} <= set(document_field['options'])
    assert 'do not create or alter official documents' in data['requirements']['safety_note'].lower()


def test_aadhaar_pvc_order_has_clean_name_and_specific_required_fields(client):
    from app.models.service import Category, Service
    from app.utils.database import db

    with client.application.app_context():
        category = Category.query.filter_by(name='Identity & Citizen Documents').first()
        if category is None:
            category = Category(name='Identity & Citizen Documents')
            db.session.add(category)
            db.session.flush()
        if Service.query.filter_by(name='Aadhaar PVC Card Order').first() is None:
            db.session.add(Service(
                name='Aadhaar PVC Card Order',
                description='Help with ordering an Aadhaar PVC card through UIDAI.',
                keywords='aadhaar pvc aadhar pvc uidai pvc card order',
                category_id=category.id,
                is_active=True,
            ))
            db.session.commit()

    response = client.get('/api/services/search?q=aadhaar pvc')

    assert response.status_code == 200
    service = next(item for item in response.get_json() if item['name'] == 'Aadhaar PVC Card Order')
    assert 'Guidance' not in service['name']
    assert not service['name'].endswith('Order Apply')
    assert service['slug'] == 'aadhaar-pvc-card-order'

    detail = client.get(f"/api/services/{service['id']}").get_json()
    fields = {field['key']: field for field in detail['requirements']['fields']}
    assert {'order_type', 'linked_mobile_access', 'delivery_state', 'delivery_district', 'delivery_pincode'} <= set(fields)
    assert not any(fields[key]['required'] for key in ('order_type', 'linked_mobile_access', 'delivery_state', 'delivery_district', 'delivery_pincode'))
    assert 'OTP' in detail['requirements']['safety_note']


def test_default_catalog_services_expose_optional_application_details(client):
    services = client.get('/api/services').get_json()

    assert services
    for service in services:
        detail = client.get(f"/api/services/{service['id']}")
        assert detail.status_code == 200
        fields = detail.get_json()['requirements']['fields']
        assert fields, service['name']
        assert not any(field.get('required') for field in fields), service['name']
        assert [field['key'] for field in fields] != ['assistance_type', 'deadline'], service['name']


def test_seed_catalog_and_explicit_requirement_registry_match():
    import ast
    from pathlib import Path
    from app.utils.service_requirements import SERVICE_REQUIREMENT_PROFILE_BY_NAME

    seed_path = Path(__file__).resolve().parents[1] / 'seed.py'
    module = ast.parse(seed_path.read_text(encoding='utf-8'))
    catalog = None
    for node in ast.walk(module):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'SERVICE_CATALOG' for target in node.targets):
            catalog = ast.literal_eval(node.value)
            break

    main_path = Path(__file__).resolve().parents[1] / 'app' / 'main.py'
    main_module = ast.parse(main_path.read_text(encoding='utf-8'))
    startup_defaults = None
    for node in ast.walk(main_module):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'defaults' for target in node.targets):
            startup_defaults = ast.literal_eval(node.value)
            break

    assert catalog is not None
    assert startup_defaults is not None
    catalog_names = {item[0] for items in catalog.values() for item in items}
    startup_names = {item[1] for item in startup_defaults}
    assert set(SERVICE_REQUIREMENT_PROFILE_BY_NAME) == catalog_names | startup_names


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
    assert any(service['name'] == 'Identity Document Apply' for service in partial.get_json())
    assert any(service['name'] == 'Identity Document Apply' for service in category.get_json())
    assert any(service['name'] == 'Identity Document Apply' for service in keyword.get_json())
