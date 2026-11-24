"""Allowlisted text endpoints for provider evaluations using synthetic inputs."""
import os
import re

from .providers.base import ProviderAdapter
from .providers.errors import ProviderError
from .providers.gemini import GeminiProvider


MODELS = {
    'groq': {'client': 'openai/gpt-oss-20b', 'admin': 'openai/gpt-oss-120b'},
    'cloudflare': dict.fromkeys(('client', 'admin'), '@cf/meta/llama-3.1-8b-instruct'),
    'openrouter': dict.fromkeys(('client', 'admin'), 'openai/gpt-oss-120b:free'),
    'gemini': dict.fromkeys(('client', 'admin'), 'gemini-3.5-flash-lite'),
}
KEYS = {'groq': 'GROQ_API_KEY', 'cloudflare': 'CLOUDFLARE_API_TOKEN',
        'openrouter': 'OPENROUTER_API_KEY', 'gemini': 'GEMINI_API_KEY'}


class FreeTransport(ProviderAdapter):
    max_attempts = 1
    timeout = (2, 5)

    def __init__(self, name):
        self.name = name
        self.key_env = KEYS[name]

    def eligible(self):
        # Set only after verifying provider-side hard denial of billable usage.
        verified = os.getenv(f'POSP_{self.name.upper()}_FREE_ONLY_VERIFIED') == 'true'
        account_ok = self.name != 'cloudflare' or re.fullmatch(
            r'[0-9a-fA-F]{32}', os.getenv('CLOUDFLARE_ACCOUNT_ID', ''))
        return bool(verified and self.is_configured() and account_ok)

    def synthetic_reply(self, role, prompt):
        if role not in ('client', 'admin') or not self.eligible():
            raise ProviderError('disabled', 'Free-tier account is unverified.')
        model = MODELS[self.name][role]
        instructions = 'Answer this synthetic POSP support evaluation briefly in the requested language.'
        if self.name == 'gemini':
            return GeminiProvider().generate(instructions=instructions, prompt=prompt, model=model, max_output_tokens=256)
        messages = [{'role': 'system', 'content': instructions}, {'role': 'user', 'content': prompt}]
        body = {'messages': messages, 'max_tokens': 256}
        if self.name == 'cloudflare':
            account = os.environ['CLOUDFLARE_ACCOUNT_ID']
            url = f'https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}'
        else:
            url = {'groq': 'https://api.groq.com/openai/v1/chat/completions',
                   'openrouter': 'https://openrouter.ai/api/v1/chat/completions'}[self.name]
            body['model'] = model
            if self.name == 'openrouter':
                body['provider'] = {'max_price': {'prompt': 0, 'completion': 0},
                                    'data_collection': 'deny', 'allow_fallbacks': False}
        data = self.post_json(endpoint=url, headers={'Authorization': f'Bearer {self.api_key()}'}, payload=body)
        if self.name == 'cloudflare':
            return (data.get('result') or {}).get('response', '') if data.get('success') else ''
        choices = data.get('choices') or []
        if not choices or choices[0].get('finish_reason') != 'stop':
            return ''
        return (choices[0].get('message') or {}).get('content') or ''
