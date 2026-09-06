from app.government_services.catalog import load_verified_catalog


def test_verified_government_catalog_has_first_party_metadata():
    data = load_verified_catalog()
    assert data['schema_version'] == 1
    assert data['services']
    names = set()
    for item in data['services']:
        assert item['name'] not in names
        names.add(item['name'])
        assert item['source_name']
        assert item['source_url'].startswith('https://')
        assert item['verified_at']
        assert item.get('state', 'active') in {'active', 'retired'}
        assert item.get('official_fee_status', 'unconfirmed') in {'known', 'none', 'unconfirmed'}


def test_manifest_services_are_synced_into_public_catalog(client):
    response = client.get('/api/services/search?q=Aadhaar%20Mobile%20Number')
    assert response.status_code == 200
    items = response.get_json()
    assert any(item.get('catalog_name') == 'Aadhaar Mobile Number Update Assistance' for item in items)

    response = client.get('/api/services/search?q=PAN%20Aadhaar')
    assert response.status_code == 200
    items = response.get_json()
    assert any(item.get('catalog_name') == 'PAN - Aadhaar Linking Assistance' for item in items)


def test_known_uidai_official_fees_are_preserved(client):
    response = client.get('/api/services/search?q=Aadhaar%20PVC')
    assert response.status_code == 200
    pvc = next(item for item in response.get_json() if item.get('catalog_name') == 'Aadhaar PVC Card Order')
    assert pvc['official_fee_status'] == 'known'
    assert pvc['official_fee_inr'] == 75.0
