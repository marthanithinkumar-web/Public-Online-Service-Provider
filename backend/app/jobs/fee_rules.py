"""Structured, admin-verified fee assessment for official job notices."""

ALLOWED_FACTOR_TYPES = {'select', 'text', 'boolean'}
MAX_FACTORS = 12
MAX_RULES = 40


def normalise_fee_configuration(factors, rules):
    if not isinstance(factors, list) or len(factors) > MAX_FACTORS:
        raise ValueError('Fee factors must be a list with at most 12 items.')
    if not isinstance(rules, list) or not rules or len(rules) > MAX_RULES:
        raise ValueError('Fee rules must contain between 1 and 40 rules.')

    clean_factors = []
    seen = set()
    for raw in factors:
        if not isinstance(raw, dict):
            raise ValueError('Each fee factor must be an object.')
        key = str(raw.get('key') or '').strip().lower().replace(' ', '_')[:60]
        label = str(raw.get('label') or '').strip()[:120]
        factor_type = str(raw.get('type') or 'select').strip().lower()
        if not key or not label or key in seen:
            raise ValueError('Every fee factor needs a unique key and label.')
        if factor_type not in ALLOWED_FACTOR_TYPES:
            raise ValueError('Fee factor type must be select, text, or boolean.')
        options = []
        if factor_type == 'select':
            raw_options = raw.get('options') or []
            if not isinstance(raw_options, list) or not raw_options or len(raw_options) > 30:
                raise ValueError(f'{label} needs between 1 and 30 options.')
            options = [str(value).strip()[:100] for value in raw_options if str(value).strip()]
            if not options:
                raise ValueError(f'{label} needs at least one option.')
        clean_factors.append({'key': key, 'label': label, 'type': factor_type, 'options': options, 'required': True})
        seen.add(key)

    clean_rules = []
    for index, raw in enumerate(rules):
        if not isinstance(raw, dict):
            raise ValueError('Each fee rule must be an object.')
        try:
            amount = round(float(raw.get('amount_inr')), 2)
        except (TypeError, ValueError):
            raise ValueError(f'Fee rule {index + 1} needs a valid amount.')
        if amount < 0 or amount > 100000:
            raise ValueError('Official fee must be between ₹0 and ₹1,00,000.')
        conditions = raw.get('conditions') or {}
        if not isinstance(conditions, dict):
            raise ValueError('Fee rule conditions must use named factors.')
        clean_conditions = {}
        for key, values in conditions.items():
            key = str(key).strip().lower().replace(' ', '_')
            if key not in seen:
                raise ValueError(f'Fee rule refers to unknown factor: {key}.')
            values = values if isinstance(values, list) else [values]
            clean_values = [str(value).strip()[:100] for value in values if str(value).strip()]
            if not clean_values:
                raise ValueError(f'Fee rule condition {key} cannot be empty.')
            clean_conditions[key] = clean_values
        clean_rules.append({
            'amount_inr': amount,
            'conditions': clean_conditions,
            'label': str(raw.get('label') or f'Rule {index + 1}').strip()[:160],
            'priority': int(raw.get('priority') or 0),
        })

    return clean_factors, clean_rules


def required_factor_answers(job, answers):
    factors = job.fee_factors or []
    missing = []
    for factor in factors:
        key = factor.get('key')
        if not key:
            continue
        value = answers.get(key)
        if value is None or str(value).strip() == '':
            missing.append(factor.get('label') or key)
    return missing


def assess_official_fee(job, answers):
    """Return a verified amount only when the notice has admin-reviewed rules."""
    factors = job.fee_factors or []
    rules = job.fee_rules or []
    if not job.fee_rules_verified_at or not rules:
        return {'status': 'unconfirmed', 'amount_inr': None, 'matched_rule': None}

    missing = required_factor_answers(job, answers)
    if missing:
        return {'status': 'missing_factors', 'amount_inr': None, 'missing': missing, 'matched_rule': None}

    matches = []
    for order, rule in enumerate(rules):
        conditions = rule.get('conditions') or {}
        matched = True
        for key, accepted in conditions.items():
            actual = str(answers.get(key) or '').strip().casefold()
            accepted_values = {str(value).strip().casefold() for value in accepted}
            if actual not in accepted_values:
                matched = False
                break
        if matched:
            matches.append((int(rule.get('priority') or 0), len(conditions), -order, rule))

    if not matches:
        return {'status': 'no_match', 'amount_inr': None, 'matched_rule': None}
    matches.sort(reverse=True, key=lambda item: item[:3])
    rule = matches[0][3]
    return {
        'status': 'known',
        'amount_inr': round(float(rule['amount_inr']), 2),
        'matched_rule': rule.get('label'),
    }
