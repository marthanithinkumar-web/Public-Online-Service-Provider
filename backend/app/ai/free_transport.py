"""Allowlisted text endpoints for provider evaluations using synthetic inputs."""
import json
import os
from time import monotonic
import re
from decimal import Decimal, InvalidOperation

import requests

from .text import extract_gemini_text
from .providers.base import ProviderAdapter
from .providers.errors import ProviderError
from .providers.gemini import GeminiProvider


MODELS = {
    'groq': {'client': 'openai/gpt-oss-20b', 'admin': 'openai/gpt-oss-120b'},
    'cloudflare': dict.fromkeys(('client', 'admin'), '@cf/meta/llama-3.1-8b-instruct'),
    'openrouter': dict.fromkeys(('client', 'admin'), 'google/gemma-4-26b-a4b-it:free'),
    'gemini': dict.fromkeys(('client', 'admin'), 'gemini-3.5-flash-lite'),
}
KEYS = {'groq': 'GROQ_API_KEY', 'cloudflare': 'CLOUDFLARE_API_TOKEN',
        'openrouter': 'OPENROUTER_API_KEY', 'gemini': 'GEMINI_API_KEY'}


def verified_free_listing(model):
    if not model.endswith(':free'):
        return False
    try:
        response = requests.get('https://openrouter.ai/api/v1/models', timeout=(2, 3), allow_redirects=False)
        response.raise_for_status()
        for item in response.json()['data']:
            if item.get('id') != model:
                continue
            prices = item['pricing']
            return {'prompt', 'completion'} <= prices.keys() and all(
                Decimal(str(price)) == 0 for price in prices.values())
    except (requests.RequestException, ValueError, KeyError, AttributeError, TypeError, InvalidOperation):
        return False
    return False


class FreeTransport(ProviderAdapter):
    max_attempts = 1
    timeout = (2, 5)

    def __init__(self, name):
        self.name = name
        self.key_env = KEYS[name]
        self.reported_tokens = None

    def _read_usage(self, usage, field='total_tokens'):
        tokens = usage.get(field) if isinstance(usage, dict) else None
        self.reported_tokens = tokens if type(tokens) is int and tokens >= 0 else None

    def eligible(self):
        # Set only after verifying provider-side hard denial of billable usage.
        if os.getenv('POSP_AI_ENABLED', 'true').strip().lower() not in {'true', 'yes', '1'}:
            return False
        if os.getenv('POSP_AI_PROVIDER', '').strip().lower() == 'disabled':
            return False
        verified = os.getenv(f'POSP_{self.name.upper()}_FREE_ONLY_VERIFIED') == 'true'
        account_ok = self.name != 'cloudflare' or re.fullmatch(
            r'[0-9a-fA-F]{32}', os.getenv('CLOUDFLARE_ACCOUNT_ID', ''))
        return bool(verified and self.is_configured() and account_ok)

    def stream_fixture(self, role, language):
        if self.name != 'groq' or not self.eligible():
            raise ProviderError('disabled', 'Free streaming is unavailable.')
        if role not in ('client', 'admin') or language not in ('English', 'Hindi', 'Telugu'):
            raise ProviderError('disabled', 'Unknown evaluation configuration.')
        prompt = f'Explain in {language} that the fixture assistance fee is 73 INR.'
        payload = {'model': MODELS['groq'][role], 'max_tokens': 256, 'stream': True,
                   'messages': [{'role': 'user', 'content': prompt}]}
        deadline = monotonic() + 12
        with requests.post('https://api.groq.com/openai/v1/chat/completions',
                           headers={'Authorization': f'Bearer {self.api_key()}'}, json=payload,
                           stream=True, timeout=self.timeout, allow_redirects=False) as response:
            if response.status_code != 200:
                raise ProviderError('unavailable', 'Free streaming provider is unavailable.')
            size = 0
            pending = b''
            answered = finished = False
            for chunk in response.iter_content(chunk_size=128):
                size += len(chunk)
                if size > 65536 or monotonic() > deadline:
                    break
                lines = (pending + chunk).split(b'\n')
                pending = lines.pop()
                for line in lines:
                    if not line.startswith(b'data:'):
                        continue
                    event = line[5:].strip()
                    if event == b'[DONE]':
                        if finished and answered:
                            return
                        raise ProviderError('invalid_response', 'Incomplete provider stream.')
                    data = json.loads(event)
                    usage = data.get('usage') or (data.get('x_groq') or {}).get('usage')
                    if usage is not None:
                        self._read_usage(usage)
                    for choice in data.get('choices') or []:
                        piece = (choice.get('delta') or {}).get('content')
                        if isinstance(piece, str) and piece:
                            answered = True
                            yield piece
                        if choice.get('finish_reason') == 'stop':
                            finished = True
        raise ProviderError('invalid_response', 'Incomplete provider stream.')

    def synthetic_reply(self, role, prompt):
        self.reported_tokens = None
        if role not in ('client', 'admin') or not self.eligible():
            raise ProviderError('disabled', 'Free-tier account is unverified.')
        model = MODELS[self.name][role]
        instructions = 'Answer this synthetic POSP support evaluation briefly in the requested language.'
        if self.name == 'gemini':
            adapter = GeminiProvider()
            adapter.max_attempts = self.max_attempts
            adapter.timeout = self.timeout
            data = adapter.generate_payload(instructions=instructions, prompt=prompt, model=model, max_output_tokens=256)
            self._read_usage(data.get("usageMetadata"), "totalTokenCount")
            return extract_gemini_text(data)
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
                if not verified_free_listing(model):
                    raise ProviderError('disabled', 'Free model pricing could not be verified.')
                body['provider'] = {'max_price': {'prompt': 0, 'completion': 0},
                                    'data_collection': 'deny', 'allow_fallbacks': False}
        data = self.post_json(endpoint=url, headers={'Authorization': f'Bearer {self.api_key()}'}, payload=body)
        if self.name == 'cloudflare':
            result = data.get('result') or {}
            self._read_usage(result.get('usage'))
            return result.get('response', '') if data.get('success') else ''
        self._read_usage(data.get('usage'))
        choices = data.get('choices') or []
        if not choices or choices[0].get('finish_reason') != 'stop':
            return ''
        return (choices[0].get('message') or {}).get('content') or ''
