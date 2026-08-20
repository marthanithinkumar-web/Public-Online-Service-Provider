"""Central service-request definitions used by both the API and UI.

These definitions intentionally describe assistance requirements only. They do not
collect OTPs, passwords, PINs, bank credentials, or other authentication secrets.
"""


def get_service_requirements(service):
    text = f"{service.name or ''} {service.keywords or ''} {service.category.name if getattr(service, 'category', None) else ''}".lower()

    if 'scholarship' in text or 'epass' in text:
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

    return {
        'fields': fields,
        'documents': documents,
        'safety_note': 'Never provide OTPs, passwords, PINs, CVV, banking credentials, or account recovery codes.',
    }


def validate_service_application(service, application_data):
    requirements = get_service_requirements(service)
    missing = []
    for field in requirements['fields']:
        if field.get('required') and not str(application_data.get(field['key'], '')).strip():
            missing.append(field['label'])
    return requirements, missing
