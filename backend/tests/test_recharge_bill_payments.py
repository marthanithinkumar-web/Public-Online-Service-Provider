from app.main import ensure_default_services
from app.models.service import Service
from app.utils.database import db


def _client(client):
    response=client.post('/api/auth/register',json={'name':'Recharge Client','phone':'9876543210','email':'recharge-client@example.com','password':'strong-pass'})
    return {'Authorization':f"Bearer {response.get_json()['token']}"}


def _service_id(client):
    with client.application.app_context():
        ensure_default_services()
        return Service.query.filter_by(name='Recharge & Bill Payments').first().id


def test_mobile_recharge_uses_ten_rupee_assistance_fee_and_no_official_fee(client):
    response=client.post('/api/orders/',headers=_client(client),json={'service_id':_service_id(client),'application_data':{'recharge_bill_type':'mobile_prepaid','customer_reference':'9876543210','operator':'Jio','circle':'Telangana','plan_reference':'₹299 plan','recharge_amount':299}})
    assert response.status_code==201
    order=response.get_json()['order']
    assert order['fee_inr']==10
    assert order['official_fee_inr']==0
    assert order['official_fee_status']=='none'


def test_mobile_recharge_rejects_invalid_number(client):
    response=client.post('/api/orders/',headers=_client(client),json={'service_id':_service_id(client),'application_data':{'recharge_bill_type':'mobile_prepaid','customer_reference':'12345','operator':'Airtel','circle':'Telangana','plan_reference':'Plan'}})
    assert response.status_code==409
    assert '10-digit Indian mobile number' in response.get_json()['error']


def test_mobile_recharge_requires_operator_and_circle_instead_of_prefix_guessing(client):
    headers=_client(client);service_id=_service_id(client)
    response=client.post('/api/orders/',headers=headers,json={'service_id':service_id,'application_data':{'recharge_bill_type':'mobile_prepaid','customer_reference':'9876543210','plan_reference':'Plan'}})
    assert response.status_code==409
    assert 'Airtel, Jio, Vi, or BSNL' in response.get_json()['error']


def test_bill_payment_requires_biller_and_customer_reference(client):
    response=client.post('/api/orders/',headers=_client(client),json={'service_id':_service_id(client),'application_data':{'recharge_bill_type':'electricity','customer_reference':'123456789'}})
    assert response.status_code==409
    assert 'biller/provider' in response.get_json()['error']


def test_supported_bill_payment_is_assistance_only_until_authorized_integration(client):
    response=client.post('/api/orders/',headers=_client(client),json={'service_id':_service_id(client),'application_data':{'recharge_bill_type':'electricity','biller':'Example Electricity Board','customer_reference':'123456789','recharge_amount':850}})
    assert response.status_code==201
    order=response.get_json()['order']
    assert order['fee_inr']==10
    assert order['official_fee_inr']==0
    assert order['official_fee_status']=='none'
