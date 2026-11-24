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
    if re.search(r'payment|refund|approval|complaint|human|भुगतान|చెల్లింపు', text):
        return handoff, True, None
    if re.search(r'\bjobs?\b|vacanc|नौकरी|नौकरि|ఉద్యోగ', text):
        return f'{jobs}: https://pospindia.onrender.com/jobs. {handoff}', True, None
    if re.search(r'scholarship|छात्रवृत्ति|స్కాలర్|ఉపకార', text):
        return f'{scholarships}: https://pospindia.onrender.com/scholarships. {handoff}', True, None
    services = context.get('relevant_services') or []
    named = [s for s in services if s.get('name') and s['name'].casefold() in text]
    if not named and len(services) == 1 and re.search(r'\bits\b|उसका|దాని', text):
        history = context.get('recent_conversation') or []
        if any(services[0]['name'].casefold() in row.get('content', '').casefold()
               for row in history[-1:] if row.get('role') == 'client'):
            named = services
    if len(named) == 1:
        service = named[0]
        if re.search(r'official|government fee|सरकारी|ప్రభుత్వ', text):
            return handoff, True, None
        if re.search(r'fee|शुल्क|రుసుము|ఫీజు', text) and service.get('application_fee_inr') is not None:
            return f"{service['name']} — {fee_label}: ₹{service['application_fee_inr']}.", False, None
        if re.search(r'how.*apply|procedure|आवेदन|దరఖాస్తు', text) and service.get('description'):
            return f"{service['name']}: {service['description']}", False, None
    return handoff, True, None
