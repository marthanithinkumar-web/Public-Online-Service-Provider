from app.routes.ai_operations import _extract_response_text


def test_extract_response_text_reads_responses_api_output():
    payload = {
        'output': [
            {'type': 'message', 'content': [
                {'type': 'output_text', 'text': 'POSP is healthy.'},
            ]},
        ],
    }
    assert _extract_response_text(payload) == 'POSP is healthy.'


def test_extract_response_text_returns_empty_for_missing_text():
    assert _extract_response_text({'output': []}) == ''


def test_parse_client_ai_response_detects_handoff():
    from app.routes.ai_operations import _parse_client_ai_response
    answer, handoff = _parse_client_ai_response('HANDOFF=YES\nANSWER=I will connect you with the service team.')
    assert handoff is True
    assert answer == 'I will connect you with the service team.'


def test_parse_client_ai_response_keeps_safe_answer():
    from app.routes.ai_operations import _parse_client_ai_response
    answer, handoff = _parse_client_ai_response('HANDOFF=NO\nANSWER=You can track your request from your dashboard.')
    assert handoff is False
    assert answer == 'You can track your request from your dashboard.'



def test_client_ai_handoff_stays_in_private_existing_chat(client, monkeypatch):
    from app.models.user import User
    from app.routes import ai_operations, messages
    from app.utils.database import db
    from app.utils.password import hash_password

    alerts = []
    monkeypatch.setattr(
        ai_operations,
        "generate_client_reply",
        lambda user, message: ("I will connect you with the service team.", True, None),
        raising=False,
    )
    monkeypatch.setattr(messages, "send_admin_activity_alert", lambda title, message: alerts.append((title, message)))

    with client.application.app_context():
        db.session.add(User(
            name="Support Admin",
            email="ai-support-admin@example.com",
            password_hash=hash_password("test-admin-pass"),
            is_admin=True,
            is_active=True,
        ))
        db.session.commit()

    first = client.post("/api/auth/register", json={
        "name": "First Client", "phone": "9000000011",
        "email": "first-ai-client@example.com", "password": "strong-pass",
    }).get_json()["token"]
    second = client.post("/api/auth/register", json={
        "name": "Second Client", "phone": "9000000012",
        "email": "second-ai-client@example.com", "password": "strong-pass",
    }).get_json()["token"]

    response = client.post(
        "/api/messages/mine",
        json={"message": "Please connect me with a human."},
        headers={"Authorization": f"Bearer {first}"},
    )

    assert response.status_code == 201
    assert response.get_json()["ai_handoff"] is True
    first_thread = client.get(
        "/api/messages/mine", headers={"Authorization": f"Bearer {first}"}
    ).get_json()["items"]
    second_thread = client.get(
        "/api/messages/mine", headers={"Authorization": f"Bearer {second}"}
    ).get_json()["items"]
    assert [item["sender_role"] for item in first_thread] == ["client", "ai"]
    assert "connect you with the service team" in first_thread[-1]["message"]
    assert second_thread == []
    assert len(alerts) == 1
    assert "private support message" in alerts[0][1]
