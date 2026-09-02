from html import escape


def _money(value):
    return f"₹{float(value or 0):.2f}"


def receipt_data(order, payment):
    purpose = payment.purpose or 'request_total'
    assistance_total = round(float(order.fee_inr or 0), 2)
    official_total = round(float(order.official_fee_inr or 0), 2)
    paid_total = round(payment.amount_paise / 100, 2)
    assistance_paid = paid_total if purpose == 'assistance_fee' else (assistance_total if purpose == 'request_total' else 0.0)
    official_paid = paid_total if purpose == 'official_fee' else (official_total if purpose == 'request_total' else 0.0)
    captured_at = payment.captured_at or payment.updated_at or payment.created_at
    label = {
        'assistance_fee': 'Assistance fee payment',
        'official_fee': 'Official/government fee payment',
        'request_total': 'Combined assistance and official fee payment',
    }.get(purpose, 'Request payment')
    return {
        'receipt_number': f'POSP-RCP-{payment.id:06d}',
        'order_code': order.order_code,
        'client_name': order.client_name,
        'client_email': order.email or '',
        'service': order.service.name if order.service else 'Service assistance',
        'purpose': purpose,
        'purpose_label': label,
        'assistance_fee_inr': assistance_paid,
        'official_fee_inr': official_paid,
        'total_paid_inr': paid_total,
        'currency': payment.currency,
        'provider': 'Razorpay',
        'razorpay_order_id': payment.razorpay_order_id,
        'razorpay_payment_id': payment.razorpay_payment_id or '',
        'captured_at': captured_at.isoformat() if captured_at else '',
    }


def receipt_text(order, payment):
    data = receipt_data(order, payment)
    return (
        'PAYMENT RECEIPT\n'
        'Public Online Service Provider\n\n'
        f"Receipt: {data['receipt_number']}\n"
        f"Request: {data['order_code']}\n"
        f"Payment type: {data['purpose_label']}\n"
        f"Client: {data['client_name']}\n"
        f"Service: {data['service']}\n"
        f"Paid at: {data['captured_at']}\n\n"
        f"Assistance fee paid in this transaction: {_money(data['assistance_fee_inr'])}\n"
        f"Official/government fee paid in this transaction: {_money(data['official_fee_inr'])}\n"
        f"Total paid: {_money(data['total_paid_inr'])}\n\n"
        f"Razorpay payment ID: {data['razorpay_payment_id']}\n"
        f"Razorpay order ID: {data['razorpay_order_id']}\n\n"
        'This receipt confirms the amount collected by Public Online Service Provider. '
        'It is not the official government portal fee receipt. When an official portal issues '
        'a separate acknowledgement or fee receipt, that document should be provided with the application record.\n'
    )


def receipt_html(order, payment):
    data = receipt_data(order, payment)
    safe = {key: escape(str(value)) for key, value in data.items()}
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Payment receipt {safe['receipt_number']}</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#f4f6f8;color:#17202a}}
main{{max-width:760px;margin:32px auto;background:white;padding:32px;border:1px solid #dfe5eb;border-radius:12px}}
h1{{margin:0 0 4px}} .muted{{color:#5f6b76}} table{{width:100%;border-collapse:collapse;margin:24px 0}}
th,td{{padding:12px 8px;border-bottom:1px solid #e7ebef;text-align:left}} td:last-child{{text-align:right}} .total{{font-size:1.15rem;font-weight:700}} .notice{{background:#f7f9fb;padding:14px;border-radius:8px}} .actions{{margin-top:24px}} button{{padding:10px 16px;cursor:pointer}} @media print{{body{{background:white}}main{{margin:0;border:0;box-shadow:none}}.actions{{display:none}}}}
</style>
</head>
<body><main>
<h1>Payment Receipt</h1><div class="muted">Public Online Service Provider</div>
<p><strong>Receipt:</strong> {safe['receipt_number']}<br><strong>Request:</strong> {safe['order_code']}<br><strong>Payment type:</strong> {safe['purpose_label']}<br><strong>Paid at:</strong> {safe['captured_at']}</p>
<p><strong>Client:</strong> {safe['client_name']}<br><strong>Service:</strong> {safe['service']}</p>
<table><tbody>
<tr><th>Assistance fee paid in this transaction</th><td>{_money(data['assistance_fee_inr'])}</td></tr>
<tr><th>Official/government fee paid in this transaction</th><td>{_money(data['official_fee_inr'])}</td></tr>
<tr class="total"><th>Total paid</th><td>{_money(data['total_paid_inr'])}</td></tr>
</tbody></table>
<p><strong>Razorpay payment ID:</strong> {safe['razorpay_payment_id']}<br><strong>Razorpay order ID:</strong> {safe['razorpay_order_id']}</p>
<p class="notice">This receipt confirms the amount collected by Public Online Service Provider. It is not the official government portal fee receipt. Any separate acknowledgement or fee receipt issued by the official portal should be provided with the application record.</p>
<div class="actions"><button onclick="window.print()">Print / Save as PDF</button></div>
</main></body></html>'''
