def _answer(answers, key):
    value = answers.get(key)
    return str(value).strip().lower() if value is not None else ''


def assess_scholarship(item, answers):
    """Return conservative eligibility guidance from facts explicitly present in the catalog.

    This never replaces the source portal's final eligibility decision. Rules are intentionally
    limited to conditions that are clear from a scholarship title/summary so we do not invent
    scheme requirements that are not stored in the verified catalog.
    """
    if not isinstance(answers, dict):
        answers = {}

    title = str(item.get('title') or '').lower()
    eligibility = str(item.get('eligibility') or '').lower()
    text = f'{title} {eligibility}'
    checks = []
    missing = []

    def require(key, label, expected):
        value = _answer(answers, key)
        if not value:
            missing.append(key)
            return
        ok = value in expected
        checks.append({'field': key, 'label': label, 'matched': ok})

    if 'girl student' in text or 'girl students' in text:
        require('gender', 'Girl student', {'female', 'girl', 'woman'})
    if 'disabilit' in text or 'specially abled' in text:
        require('disability', 'Student with disability', {'yes', 'true', '1'})
    if 'obc, ebc and dnt' in text or ('obc' in text and 'ebc' in text and 'dnt' in text):
        require('social_category', 'OBC, EBC or DNT category', {'obc', 'ebc', 'dnt'})
    if 'st student' in text or 'st students' in text or 'schedule tribe' in text:
        require('social_category', 'Scheduled Tribe category', {'st', 'scheduled tribe', 'scheduled tribe (st)'})
    if 'north eastern region' in text:
        region = _answer(answers, 'region')
        if not region:
            missing.append('region')
        else:
            ne_terms = ('arunachal', 'assam', 'manipur', 'meghalaya', 'mizoram', 'nagaland', 'sikkim', 'tripura', 'north east', 'northeast')
            checks.append({'field': 'region', 'label': 'North Eastern Region', 'matched': any(term in region for term in ne_terms)})

    failed = [check for check in checks if not check['matched']]
    if failed:
        status = 'not_matched'
    elif missing:
        status = 'needs_more_information'
    else:
        status = 'potentially_eligible'

    return {
        'status': status,
        'checks': checks,
        'missing_fields': sorted(set(missing)),
        'official_verification_required': True,
        'message': (
            'Your details do not match one or more clearly stated conditions for this scholarship.' if status == 'not_matched'
            else 'Add the remaining details to improve the eligibility check.' if status == 'needs_more_information'
            else 'Your details match the conditions we can verify from the current listing. Confirm every requirement on the source portal before applying.'
        ),
    }
