def test_allowed_api_preflight_is_cached_for_ten_minutes(client):
    response = client.options(
        '/api/auth/login',
        headers={
            'Origin': 'https://pospindia.onrender.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type',
        },
    )
    assert response.status_code == 200
    assert response.headers.get('Access-Control-Allow-Origin') == 'https://pospindia.onrender.com'
    assert response.headers.get('Access-Control-Max-Age') == '600'
