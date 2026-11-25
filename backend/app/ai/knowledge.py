"""Local support answers from catalog facts; never calls a provider."""
import re


def support_answer(context, question):
    language = 'te' if re.search(r'[ఀ-౿]', question) else 'hi' if re.search(r'[ऀ-ॿ]', question) else 'en'
    messages = {
        'en': ('The service team can verify this for you.', 'POSP assistance fee', 'Browse verified jobs', 'Browse verified scholarships'),
        'hi': ('सेवा टीम इसकी पुष्टि कर सकती है।', 'POSP सहायता शुल्क', 'सत्यापित नौकरियाँ देखें', 'सत्यापित छात्रवृत्तियाँ देखें'),
        'te': ('దీనిని సేవా బృందం నిర్ధారించగలదు.', 'POSP సహాయ రుసుము', 'ధృవీకరించిన ఉద్యోగాలు', 'ధృవీకరించిన ఉపకార వేతనాలు'),
    }
    handoff, fee_label, jobs, scholarships = messages[language]
    text = question.casefold()
    if re.search(r'payment|refund|approval|complaint|human|administrator|\badmin\b|agent|staff|service team|भुगतान|कर्मचारी|प्रतिनिधि|చెల్లింపు|సిబ్బంది|ప్రతినిధి', text):
        return handoff, True, None
    for kind, pattern, label in (
        ('jobs', r'\bjobs?\b|vacanc|नौकरी|नौकरि|ఉద్యోగ', jobs),
        ('scholarships', r'scholarship|छात्रवृत्ति|స్కాలర్|ఉపకార', scholarships),
    ):
        if not re.search(pattern, text):
            continue
        directory = f'https://pospindia.onrender.com/{kind}'
        entries = []
        for item in context.get(f'active_{kind}_verified') or []:
            link = item.get('official_notice_url') or item.get('source_url') or ''
            checked = item.get('source_checked_at')
            if not checked or not link.startswith('https://') or not item.get('title'):
                continue
            parts = [item['title'], item.get('status_label'), item.get('qualification') or item.get('education_level'),
                     item.get('location') or item.get('region'), item.get('deadline'), link, str(checked)[:10]]
            entries.append(' · '.join(str(value) for value in parts if value))
        if not entries:
            return f'{label}: {directory}. {handoff}', True, None
        return '\n'.join([f'{label}: {directory}', *entries[:3]]), False, None
    services = context.get('relevant_services') or []
    named = [s for s in services if s.get('name') and s['name'].casefold() in text]
    if not named and re.search(r'\bits\b|उसका|దాని', text):
        history = context.get('recent_conversation') or []
        prior = [row.get('content', '') for row in history if row.get('role') == 'client']
        if prior and prior[-1] == question[:320]:
            prior.pop()
        if prior:
            named = [s for s in services if s.get('name') and s['name'].casefold() in prior[-1].casefold()]
    if len(named) == 1:
        service = named[0]
        intent = text.replace(service['name'].casefold(), ' ')
        if re.search(r'official|government fee|सरकारी|ప్రభుత్వ', intent):
            fee_question = re.search(r'\bfees?\b|शुल्क|రుసుము|ఫీజు', intent)
            status = service.get('official_fee_status')
            amount = service.get('official_fee_inr')
            if fee_question and status in ('known', 'none') and amount is not None:
                if status == 'none' and amount != 0:
                    return handoff, True, None
                official_label = {'en': 'Official fee', 'hi': 'सरकारी शुल्क', 'te': 'ప్రభుత్వ రుసుము'}[language]
                return f"{service['name']} — {official_label}: ₹{amount}.", False, None
            return handoff, True, None
        if re.search(r'fee|शुल्क|రుసుము|ఫీజు', text) and service.get('application_fee_inr') is not None:
            return f"{service['name']} — {fee_label}: ₹{service['application_fee_inr']}.", False, None
        if re.search(r'how.*apply|procedure|आवेदन|దరఖాస్తు', text) and service.get('description'):
            return f"{service['name']}: {service['description']}", False, None
    return handoff, True, None
