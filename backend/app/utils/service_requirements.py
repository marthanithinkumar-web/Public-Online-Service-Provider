"""Central service-request definitions used by both the API and UI.

These definitions intentionally describe assistance requirements only. They do not
collect OTPs, passwords, PINs, bank credentials, or other authentication secrets.
"""


def get_service_requirements(service):
    service_text = f"{service.name or ''} {service.keywords or ''}".lower()
    text = f"{service_text} {service.category.name if getattr(service, 'category', None) else ''}".lower()

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
    elif 'aadhaar pvc' in text or 'aadhar pvc' in text:
        fields = [
            {
                'key': 'order_type',
                'label': 'Order type',
                'type': 'select',
                'options': ['New PVC card order', 'PVC card re-order / replacement'],
                'required': True,
            },
            {
                'key': 'linked_mobile_access',
                'label': 'Can you access the mobile linked to Aadhaar?',
                'type': 'select',
                'options': ['Yes', 'No', 'Not sure'],
                'required': True,
            },
            {'key': 'delivery_state', 'label': 'Delivery state', 'required': True},
            {'key': 'delivery_district', 'label': 'Delivery district', 'required': True},
            {'key': 'delivery_pincode', 'label': 'Delivery PIN code', 'required': True},
        ]
        documents = ['Masked Aadhaar copy only if the service team requests it; do not upload OTP screenshots']
    elif any(x in text for x in ('passport - new', 'passport - renewal', 'passport renewal', 'passport reissue')):
        fields = [
            {
                'key': 'passport_service',
                'label': 'Passport service required',
                'type': 'select',
                'options': ['New passport', 'Renewal', 'Reissue after expiry', 'Lost / damaged passport', 'Details correction'],
                'required': True,
            },
            {'key': 'applicant_dob', 'label': 'Applicant date of birth', 'type': 'date', 'required': True},
            {'key': 'state_district', 'label': 'State / district', 'required': True},
            {'key': 'preferred_passport_office', 'label': 'Preferred Passport Seva Kendra / city', 'required': False},
            {
                'key': 'processing_preference',
                'label': 'Processing preference',
                'type': 'select',
                'options': ['Normal', 'Tatkaal (if eligible)', 'Not sure'],
                'required': True,
            },
        ]
        documents = ['Date-of-birth proof', 'Current address proof', 'Existing passport for renewal/reissue', 'Supporting document for any requested correction']
    elif any(x in text for x in ('driving licence', 'driving license', 'learner licence', 'vehicle service', 'vehicle registration', ' rc ')):
        fields = [
            {
                'key': 'transport_service',
                'label': 'Transport service required',
                'type': 'select',
                'options': ['Learner licence', 'Driving licence', 'Licence renewal', 'Address / details change', 'Vehicle RC service', 'Duplicate document', 'Other'],
                'required': True,
            },
            {'key': 'vehicle_class', 'label': 'Vehicle class / type', 'required': True},
            {'key': 'state_rto', 'label': 'State and RTO', 'required': True},
            {'key': 'existing_reference', 'label': 'Existing application/reference number (if available)', 'required': False},
        ]
        documents = ['Identity proof', 'Address proof', 'Age proof where applicable', 'Existing licence or RC for renewal/correction services']
    elif 'student bus pass' in text or 'concession bus pass' in text:
        fields = [
            {'key': 'institution', 'label': 'School / college', 'required': True},
            {'key': 'course_class', 'label': 'Course / class', 'required': True},
            {'key': 'route', 'label': 'Travel route', 'placeholder': 'From and to', 'required': True},
        ]
        documents = ['Recent passport-size photo', 'Aadhaar or other identity proof', 'Institution ID, admission receipt or bonafide certificate', 'Date-of-birth proof', 'Current address proof']
    elif 'general bus pass' in text:
        fields = [
            {'key': 'pass_type', 'label': 'Pass type', 'required': True},
            {'key': 'route', 'label': 'Travel route', 'placeholder': 'From and to', 'required': True},
        ]
        documents = ['Recent passport-size photo', 'Aadhaar or other identity proof', 'Current address proof']
    elif any(x in text for x in ('railway ticket', 'bus ticket')):
        fields = [
            {'key': 'journey_from', 'label': 'Travelling from', 'required': True},
            {'key': 'journey_to', 'label': 'Travelling to', 'required': True},
            {'key': 'journey_date', 'label': 'Preferred travel date', 'type': 'date', 'required': True},
            {'key': 'passengers', 'label': 'Number of passengers', 'required': True},
            {'key': 'travel_preference', 'label': 'Class / travel preference', 'placeholder': 'Preferred class or service type', 'required': False},
        ]
        documents = []
    elif any(x in service_text for x in ('government job', 'state government job', 'police / defence', 'recruitment application', 'apprenticeship')):
        fields = [
            {'key': 'recruitment_name', 'label': 'Recruitment / notification name', 'required': True},
            {'key': 'post_name', 'label': 'Post applying for', 'required': True},
            {'key': 'qualification', 'label': 'Highest relevant qualification', 'required': True},
            {'key': 'applicant_dob', 'label': 'Applicant date of birth', 'type': 'date', 'required': True},
            {'key': 'category', 'label': 'Reservation category (if applicable)', 'required': False},
            {'key': 'deadline', 'label': 'Application deadline', 'type': 'date', 'required': True},
            {
                'key': 'application_type',
                'label': 'Assistance required',
                'type': 'select',
                'options': ['New application', 'Application correction', 'Status check', 'Document upload', 'Other'],
                'required': True,
            },
        ]
        documents = ['Recent photograph', 'Signature image', 'Identity proof', 'Qualification certificates / marks memos', 'Category or eligibility certificate where applicable']
    elif any(x in text for x in ('epfo', 'uan', 'epf ', 'e-shram', 'eshram', 'esic', 'career service')):
        fields = [
            {'key': 'assistance_type', 'label': 'Employment service needed', 'required': True},
            {'key': 'member_status', 'label': 'Registration / membership status', 'required': True},
            {'key': 'employer_status', 'label': 'Current / previous employer status', 'required': False},
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
            {'key': 'state_district', 'label': 'State / district', 'required': True},
            {'key': 'student_category', 'label': 'Student category / community (if applicable)', 'required': False},
            {'key': 'family_income_range', 'label': 'Annual family-income range', 'required': True},
            {'key': 'previous_application_reference', 'label': 'Previous application reference (renewals only)', 'required': False},
        ]
        documents = ['Student/Applicant ID or equivalent', 'Recent academic record/marks memo', 'Income and community certificate where applicable', 'Bonafide / admission document', 'Recent photograph']
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
            {
                'key': 'update_type',
                'label': 'Aadhaar assistance type',
                'type': 'select',
                'options': ['Name update', 'Address update', 'Date-of-birth update', 'Gender update', 'Mobile / email update information', 'Document update', 'Status / appointment help'],
                'required': True,
            },
            {'key': 'state_district', 'label': 'State / district', 'required': True},
            {'key': 'supporting_document_type', 'label': 'Supporting document available', 'required': True},
            {'key': 'deadline', 'label': 'Deadline (if any)', 'type': 'date', 'required': False},
        ]
        documents = ['Aadhaar document/details relevant to the requested update']
    elif 'pan' in text:
        fields = [
            {'key': 'application_type', 'label': 'PAN assistance type', 'placeholder': 'New / correction / reprint', 'required': True},
            {'key': 'correction_needed', 'label': 'Correction/details needed', 'required': False},
            {'key': 'applicant_dob', 'label': 'Applicant date of birth', 'type': 'date', 'required': True},
            {'key': 'applicant_type', 'label': 'Applicant type', 'type': 'select', 'options': ['Individual', 'Firm / company', 'Trust / association', 'Other'], 'required': True},
            {'key': 'delivery_state', 'label': 'Delivery state', 'required': True},
        ]
        documents = ['Aadhaar or other identity proof', 'Date-of-birth proof', 'Current address proof', 'Recent photo and signature, when applicable']
    elif 'voter' in text:
        fields = [
            {'key': 'application_type', 'label': 'Voter service type', 'placeholder': 'New registration / correction / address change', 'required': True},
            {'key': 'state', 'label': 'State', 'required': True},
            {'key': 'district_constituency', 'label': 'District / constituency', 'required': True},
            {'key': 'applicant_dob', 'label': 'Applicant date of birth', 'type': 'date', 'required': True},
            {'key': 'existing_epic_status', 'label': 'Existing EPIC/Voter ID status', 'type': 'select', 'options': ['Not issued', 'Available', 'Lost / damaged', 'Not sure'], 'required': True},
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
    elif 'income certificate' in text:
        fields = [
            {'key': 'purpose', 'label': 'Purpose', 'required': True},
            {'key': 'district', 'label': 'District', 'required': True},
            {'key': 'mandal_taluk', 'label': 'Mandal / taluk', 'required': True},
            {'key': 'family_income_range', 'label': 'Approximate annual family-income range', 'required': True},
            {'key': 'applicant_dob', 'label': 'Applicant date of birth', 'type': 'date', 'required': True},
        ]
        documents = ['Aadhaar', 'Ration card or voter ID', 'Income proof or self-declaration', 'Completed application form, if available']
    elif any(x in text for x in ('caste certificate', 'community certificate')):
        fields = [
            {'key': 'community', 'label': 'Community / caste', 'required': True},
            {'key': 'district', 'label': 'District', 'required': True},
            {'key': 'mandal_taluk', 'label': 'Mandal / taluk', 'required': True},
            {'key': 'purpose', 'label': 'Purpose of certificate', 'required': True},
            {'key': 'family_certificate_status', 'label': 'Family caste/community certificate available?', 'type': 'select', 'options': ['Yes', 'No', 'Not sure'], 'required': True},
        ]
        documents = ['Aadhaar, ration card or voter ID', 'Family caste certificate, if available', 'SSC memo, date-of-birth certificate or transfer certificate', 'Study certificates', 'Required caste declaration forms, when applicable']
    elif any(x in text for x in ('residence certificate', 'domicile certificate', 'nativity')):
        fields = [
            {'key': 'purpose', 'label': 'Purpose', 'required': True},
            {'key': 'district', 'label': 'District', 'required': True},
            {'key': 'mandal_taluk', 'label': 'Mandal / taluk', 'required': True},
            {'key': 'years_of_residence', 'label': 'Years residing in the state / district', 'required': True},
            {'key': 'residence_proof_type', 'label': 'Residence proof available', 'required': True},
        ]
        documents = ['Aadhaar', 'Current residence proof: ration card, voter ID, utility bill, property document or registered rent agreement', 'Study certificate or other local-residence proof, when required']
    elif 'birth certificate' in text:
        fields = [
            {'key': 'child_name', 'label': 'Child / person name', 'required': True},
            {'key': 'date_of_birth', 'label': 'Date of birth', 'type': 'date', 'required': True},
            {'key': 'place_of_birth', 'label': 'Place and institution of birth', 'required': True},
            {'key': 'parent_names', 'label': 'Parent / guardian names', 'required': True},
            {'key': 'registration_status', 'label': 'Birth registration status', 'type': 'select', 'options': ['Already registered', 'Late registration required', 'Correction required', 'Not sure'], 'required': True},
            {'key': 'district_local_body', 'label': 'District and local body / municipality', 'required': True},
        ]
        documents = ['Hospital birth record or discharge summary', 'Parent/guardian identity documents', 'Address proof', 'Existing birth record for correction requests']
    elif 'death certificate' in text:
        fields = [
            {'key': 'deceased_name', 'label': 'Deceased person name', 'required': True},
            {'key': 'date_of_death', 'label': 'Date of death', 'type': 'date', 'required': True},
            {'key': 'place_of_death', 'label': 'Place and institution of death', 'required': True},
            {'key': 'applicant_relationship', 'label': 'Applicant relationship to deceased', 'required': True},
            {'key': 'registration_status', 'label': 'Death registration status', 'type': 'select', 'options': ['Already registered', 'Late registration required', 'Correction required', 'Not sure'], 'required': True},
            {'key': 'district_local_body', 'label': 'District and local body / municipality', 'required': True},
        ]
        documents = ['Hospital/death record where available', 'Applicant identity proof', 'Deceased person identity document where available', 'Existing death record for correction requests']
    elif 'marriage certificate' in text:
        fields = [
            {'key': 'marriage_date', 'label': 'Date of marriage', 'type': 'date', 'required': True},
            {'key': 'marriage_place', 'label': 'Place of marriage', 'required': True},
            {'key': 'spouse_names', 'label': 'Names of both spouses', 'required': True},
            {'key': 'marriage_type', 'label': 'Marriage / registration type', 'type': 'select', 'options': ['Hindu Marriage Act', 'Special Marriage Act', 'Other / not sure'], 'required': True},
            {'key': 'district_local_body', 'label': 'Registration district / local body', 'required': True},
        ]
        documents = ['Identity and age proof of both spouses', 'Address proof', 'Marriage photograph/invitation or supporting record', 'Witness details/documents as applicable']
    elif any(x in text for x in ('legal heir', 'family certificate')):
        fields = [
            {'key': 'deceased_name', 'label': 'Deceased person name', 'required': True},
            {'key': 'date_of_death', 'label': 'Date of death', 'type': 'date', 'required': True},
            {'key': 'applicant_relationship', 'label': 'Applicant relationship to deceased', 'required': True},
            {'key': 'legal_heirs_summary', 'label': 'Number and relationship of legal heirs', 'required': True},
            {'key': 'district', 'label': 'District', 'required': True},
        ]
        documents = ['Death certificate', 'Applicant identity/address proof', 'Family/ration-card record', 'Identity documents of legal heirs where applicable']
    elif any(x in text for x in ('disability certificate', 'udid')):
        fields = [
            {'key': 'application_type', 'label': 'Application type', 'type': 'select', 'options': ['New disability certificate / UDID', 'Renewal', 'Correction', 'Status check'], 'required': True},
            {'key': 'disability_type', 'label': 'Disability type', 'required': True},
            {'key': 'applicant_dob', 'label': 'Applicant date of birth', 'type': 'date', 'required': True},
            {'key': 'district_hospital', 'label': 'District / preferred assessment hospital', 'required': True},
            {'key': 'existing_certificate_status', 'label': 'Existing certificate status', 'type': 'select', 'options': ['None', 'Temporary', 'Permanent', 'Expired', 'Not sure'], 'required': True},
        ]
        documents = ['Identity and address proof', 'Recent photograph', 'Existing disability certificate', 'Relevant medical records requested for assessment']
    elif any(x in text for x in ('ews certificate', 'non-creamy', 'ncl', 'obc certificate')):
        fields = [
            {'key': 'certificate_service', 'label': 'Certificate required', 'required': True},
            {'key': 'purpose', 'label': 'Purpose', 'required': True},
            {'key': 'state_district', 'label': 'State / district', 'required': True},
            {'key': 'family_income_range', 'label': 'Approximate annual family-income range', 'required': True},
            {'key': 'financial_year', 'label': 'Relevant financial year', 'required': True},
        ]
        documents = ['Identity/address proof', 'Income evidence or declaration', 'Community certificate for NCL/OBC requests', 'Property/asset declaration where required']
    elif 'police clearance' in text:
        fields = [
            {'key': 'purpose', 'label': 'Purpose of police clearance', 'required': True},
            {'key': 'country_or_authority', 'label': 'Destination country / requesting authority', 'required': True},
            {'key': 'current_address_duration', 'label': 'Current address and period of residence', 'required': True},
            {'key': 'passport_status', 'label': 'Passport status', 'type': 'select', 'options': ['Available', 'Applied for', 'Not applicable'], 'required': True},
            {'key': 'deadline', 'label': 'Required-by date', 'type': 'date', 'required': False},
        ]
        documents = ['Passport where applicable', 'Identity proof', 'Current and previous address proof', 'Requesting-authority document where available']
    elif any(x in text for x in ('encumbrance certificate', 'land record', 'pahani', 'adangal')):
        fields = [
            {'key': 'property_service', 'label': 'Property / land-record service required', 'required': True},
            {'key': 'state_district', 'label': 'State / district', 'required': True},
            {'key': 'mandal_village', 'label': 'Mandal / taluk and village', 'required': True},
            {'key': 'property_reference_type', 'label': 'Survey / document / property reference available', 'required': True},
            {'key': 'search_period', 'label': 'Required search period (for EC)', 'required': False},
        ]
        documents = ['Sale deed/document number or survey details', 'Property owner identity proof where required', 'Previous land/property record if available']
    elif 'certificate' in text:
        fields = [
            {'key': 'certificate_type', 'label': 'Certificate type', 'required': True},
            {'key': 'purpose', 'label': 'Purpose of certificate', 'required': True},
            {'key': 'deadline', 'label': 'Deadline (if any)', 'type': 'date', 'required': False},
        ]
        documents = ['Identity proof', 'Address proof', 'Supporting certificate or record relevant to this application']
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
