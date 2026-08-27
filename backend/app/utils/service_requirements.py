"""Central service-request definitions used by both the API and UI.

These definitions intentionally describe assistance requirements only. They do not
collect OTPs, passwords, PINs, bank credentials, or other authentication secrets.
"""


def get_service_requirements(service):
    text = f"{service.name or ''} {service.keywords or ''} {service.category.name if getattr(service, 'category', None) else ''}".lower()

    if 'official document pdf access' in text:
        fields = [
            {
                'key': 'document_type',
                'label': 'Document PDF needed',
                'type': 'select',
                'options': [
                    'Aadhaar / e-Aadhaar', 'Voter ID / e-EPIC', 'PAN / e-PAN',
                    'ABHA Health ID', 'APAAR ID', 'DigiLocker document',
                    'Ration card', 'Driving licence', 'Vehicle RC',
                    'Income certificate', 'Caste / community certificate',
                    'Residence / domicile certificate', 'Birth certificate',
                    'Death certificate', 'Marriage certificate',
                    'Academic marksheet / certificate', 'Other official document',
                ],
                'required': True,
            },
            {'key': 'document_details', 'label': 'Document details or issuing portal (if known)', 'required': False},
            {'key': 'deadline', 'label': 'Deadline (if any)', 'type': 'date', 'required': False},
        ]
        documents = []
    elif any(x in text for x in ('railway ticket', 'bus ticket')):
        fields = [
            {'key': 'journey_from', 'label': 'Travelling from', 'required': True},
            {'key': 'journey_to', 'label': 'Travelling to', 'required': True},
            {'key': 'journey_date', 'label': 'Preferred travel date', 'type': 'date', 'required': True},
            {'key': 'passengers', 'label': 'Number of passengers', 'required': True},
            {'key': 'travel_preference', 'label': 'Class / travel preference', 'placeholder': 'Preferred class or service type', 'required': False},
        ]
        documents = []
    elif any(x in text for x in ('epfo', 'uan', 'epf ', 'e-shram', 'eshram', 'esic', 'career service')):
        fields = [
            {'key': 'assistance_type', 'label': 'Employment service needed', 'required': True},
            {'key': 'member_status', 'label': 'Registration / membership status', 'required': False},
            {'key': 'deadline', 'label': 'Deadline (if any)', 'type': 'date', 'required': False},
        ]
        documents = ['Relevant employment/member document, if required by the official process']
    elif any(x in text for x in ('udyam', 'gst ', 'fssai', 'trade licence', 'trade license', 'shop & establishment')):
        fields = [
            {'key': 'business_type', 'label': 'Business / activity type', 'required': True},
            {'key': 'assistance_type', 'label': 'Registration or licence assistance needed', 'required': True},
            {'key': 'state_district', 'label': 'State / district', 'required': True},
        ]
        documents = ['Business and identity documents required by the applicable official process']
    elif any(x in text for x in ('electricity', 'water connection', 'water bill', 'property tax', 'lpg')):
        fields = [
            {'key': 'utility_service', 'label': 'Utility / civic service needed', 'required': True},
            {'key': 'location', 'label': 'Service location / municipality', 'required': True},
            {'key': 'account_reference', 'label': 'Consumer or property reference (if available)', 'required': False},
        ]
        documents = ['Relevant account/property document if required; never share payment PINs or OTPs']
    elif any(x in text for x in ('pm-kisan', 'pm kisan', 'ayushman', 'abha', 'pension', 'welfare', 'ration card', 'labour')):
        fields = [
            {'key': 'scheme_service', 'label': 'Scheme / welfare assistance needed', 'required': True},
            {'key': 'state_district', 'label': 'State / district', 'required': True},
            {'key': 'application_status', 'label': 'New application, correction or status check', 'required': True},
        ]
        documents = ['Identity/eligibility document only if required by the official scheme']
    elif 'scholarship' in text or 'epass' in text:
        fields = [
            {'key': 'application_type', 'label': 'Application type', 'placeholder': 'Fresh or Renewal', 'required': True},
            {'key': 'course_class', 'label': 'Course / Class', 'required': True},
            {'key': 'institution', 'label': 'School / College / Institution', 'required': True},
            {'key': 'academic_year', 'label': 'Academic year', 'required': True},
        ]
        documents = ['Student/Applicant ID or equivalent', 'Recent academic record/marks memo']
    elif any(x in text for x in ('poly', 'eapcet', 'eamcet', 'ecet', 'icet', 'cet', 'neet', 'jee', 'cuet', 'exam')):
        fields = [
            {'key': 'qualification', 'label': 'Qualification / Class', 'required': True},
            {'key': 'exam_year', 'label': 'Exam year', 'required': True},
            {'key': 'category', 'label': 'Category (if applicable)', 'required': False},
            {'key': 'application_type', 'label': 'Assistance needed', 'placeholder': 'New application / correction / status', 'required': True},
        ]
        documents = ['Recent photograph', 'Identity/qualification document as applicable']
    elif 'aadhaar' in text or 'aadhar' in text:
        fields = [
            {'key': 'update_type', 'label': 'Aadhaar assistance type', 'placeholder': 'Name / address / DOB / mobile / document update', 'required': True},
            {'key': 'deadline', 'label': 'Deadline (if any)', 'type': 'date', 'required': False},
        ]
        documents = ['Aadhaar document/details relevant to the requested update']
    elif 'pan' in text:
        fields = [
            {'key': 'application_type', 'label': 'PAN assistance type', 'placeholder': 'New / correction / reprint', 'required': True},
            {'key': 'correction_needed', 'label': 'Correction/details needed', 'required': False},
        ]
        documents = ['Identity/address document as applicable']
    elif 'voter' in text:
        fields = [
            {'key': 'application_type', 'label': 'Voter service type', 'placeholder': 'New registration / correction / address change', 'required': True},
            {'key': 'state', 'label': 'State', 'required': True},
        ]
        documents = ['Identity/address document as applicable']
    elif any(x in text for x in ('gurukulam', 'navodaya', 'sainik', 'iiit', 'admission')):
        fields = [
            {'key': 'student_class', 'label': 'Student class / year', 'required': True},
            {'key': 'school', 'label': 'Current school / institution', 'required': False},
            {'key': 'admission_type', 'label': 'Admission type', 'required': True},
            {'key': 'deadline', 'label': 'Application deadline (if known)', 'type': 'date', 'required': False},
        ]
        documents = ['Student identity/previous academic record as applicable']
    elif 'certificate' in text:
        fields = [
            {'key': 'certificate_type', 'label': 'Certificate type', 'required': True},
            {'key': 'purpose', 'label': 'Purpose of certificate', 'required': True},
            {'key': 'deadline', 'label': 'Deadline (if any)', 'type': 'date', 'required': False},
        ]
        documents = ['Identity/address document as applicable']
    else:
        fields = [
            {'key': 'assistance_type', 'label': 'What assistance do you need?', 'required': True},
            {'key': 'deadline', 'label': 'Deadline (if any)', 'type': 'date', 'required': False},
        ]
        documents = []

    safety_note = 'Never provide OTPs, passwords, PINs, CVV, banking credentials, or account recovery codes.'
    if 'official document pdf access' in text:
        safety_note += ' Complete any identity verification or OTP yourself on the official portal. We do not create or alter official documents.'

    return {
        'fields': fields,
        'documents': documents,
        'safety_note': safety_note,
    }


def validate_service_application(service, application_data):
    requirements = get_service_requirements(service)
    missing = []
    for field in requirements['fields']:
        if field.get('required') and not str(application_data.get(field['key'], '')).strip():
            missing.append(field['label'])
    return requirements, missing
