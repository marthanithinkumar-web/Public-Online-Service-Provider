"""High-sensitivity service forms that need explicit safe data boundaries."""

SPECIALIZED_SERVICE_NAMES = {
    'Aadhaar - Bank Account Seeding / DBT Assistance',
    'Online Cyber Fraud Complaint Raise Assistance',
}


def get_specialized_requirements(service_name):
    if service_name == 'Aadhaar - Bank Account Seeding / DBT Assistance':
        return {
            'fields': [
                {'key': 'bank_name', 'label': 'Bank name', 'required': False},
                {'key': 'branch_ifsc', 'label': 'Branch / IFSC (if known)', 'required': False},
                {'key': 'account_holder_name', 'label': 'Account holder name', 'required': False},
                {'key': 'account_last_four', 'label': 'Bank account last 4 digits only', 'placeholder': 'Last 4 digits only — do not enter the full account number', 'required': False},
                {'key': 'aadhaar_last_four', 'label': 'Aadhaar last 4 digits only', 'placeholder': 'Last 4 digits only', 'required': False},
                {'key': 'registered_mobile', 'label': 'Mobile number for contact', 'required': False},
                {'key': 'dbt_purpose', 'label': 'DBT / benefit purpose', 'placeholder': 'Scheme or benefit for which seeding help is needed', 'required': False},
                {'key': 'seeding_request', 'label': 'Help needed', 'type': 'select', 'options': ['Seed Aadhaar with bank for DBT', 'Change DBT-enabled bank account', 'Check seeding status', 'Understand mandate / consent process'], 'required': False},
                {'key': 'current_seeding_status', 'label': 'Current seeding status (if known)', 'type': 'select', 'options': ['Not seeded', 'Seeded', 'Pending / unclear', 'Not checked'], 'required': False},
                {'key': 'old_bank_name', 'label': 'Previous DBT bank (when switching)', 'required': False},
                {'key': 'bank_consent_ready', 'label': 'Bank mandate / consent form status', 'type': 'select', 'options': ['Already submitted', 'Have form but not submitted', 'Need help finding the bank form', 'Not sure'], 'required': False},
            ],
            'documents': [
                'Masked Aadhaar copy if the bank requires identity proof',
                'Passbook front page, cancelled cheque or other bank account proof with unnecessary details hidden',
                'Bank Aadhaar-seeding mandate / consent form if already available',
                'Other identity/address proof only when the bank specifically requires it',
            ],
            'safety_note': 'For DBT, UIDAI says the bank links Aadhaar using its mandate/consent process and seeds the chosen account in the NPCI mapper. Never enter or upload a full Aadhaar number, full bank account number, OTP, UPI PIN, ATM/card PIN, CVV, banking password or transaction password here. This website assists with the process; the bank/NPCI completes and confirms seeding.',
            'official_action': {'label': 'Check Aadhaar-bank seeding status on the official service', 'url': 'https://myaadhaar.uidai.gov.in/'},
        }

    if service_name == 'Online Cyber Fraud Complaint Raise Assistance':
        return {
            'fields': [
                {'key': 'fraud_category', 'label': 'Fraud / cybercrime category', 'placeholder': 'UPI, card, investment, impersonation, social media, shopping, other', 'required': False},
                {'key': 'incident_datetime', 'label': 'Incident date and approximate time', 'required': False},
                {'key': 'amount_lost', 'label': 'Amount lost (₹), if any', 'required': False},
                {'key': 'transaction_reference', 'label': 'Transaction ID / UTR / reference', 'required': False},
                {'key': 'payment_channel', 'label': 'Bank / wallet / UPI app involved', 'required': False},
                {'key': 'suspect_details', 'label': 'Suspect phone / email / account / UPI ID / URL / social handle', 'required': False},
                {'key': 'incident_description', 'label': 'What happened', 'type': 'textarea', 'required': False},
                {'key': 'state_district', 'label': 'State / district', 'required': False},
                {'key': 'called_1930', 'label': 'Have you called cybercrime helpline 1930?', 'type': 'select', 'options': ['Yes', 'No', 'Not applicable / no financial loss'], 'required': False},
                {'key': 'ncrp_acknowledgement', 'label': 'National Cyber Crime Portal acknowledgement number (if already reported)', 'required': False},
                {'key': 'police_fir_reference', 'label': 'Police complaint / FIR reference (if any)', 'required': False},
                {'key': 'contact_number', 'label': 'Contact number', 'required': False},
            ],
            'documents': [
                'Screenshots of the fraudulent transaction, profile, website or messages',
                'Transaction receipt / statement showing the relevant transaction, with unrelated entries hidden',
                'Relevant chats, SMS messages or emails',
                'Fraudulent URLs or account/profile details saved as evidence',
                '1930 / National Cyber Crime Portal acknowledgement if already reported',
                'Police complaint / FIR acknowledgement if already available',
                'Identity proof only if required for the official complaint process',
            ],
            'safety_note': 'If money was lost, report immediately through the Government of India cybercrime helpline 1930 and National Cyber Crime Reporting Portal; do not wait for this assistance request. Never share OTPs, UPI PINs, ATM/card PINs, CVV, passwords, recovery codes or remote-access credentials with this website or a caller.',
            'official_action': {'label': 'Report cyber financial fraud now on the official portal', 'url': 'https://www.cybercrime.gov.in/Accept.aspx', 'phone': '1930'},
        }
    return None
