import pytest

from app.ai_tools.official_source_policy import OfficialSourcePolicyError, is_autonomous_publication_allowed, require_official_https


def test_official_https_source_is_allowed():
    # The policy uses the repository's approved official host registry.
    from app.jobs.official_fetch import ALLOWED_HOSTS
    host = next(iter(ALLOWED_HOSTS))
    assert require_official_https(f'https://{host}/notice')
    assert is_autonomous_publication_allowed(f'https://{host}/notice') is True


def test_non_https_source_is_rejected():
    from app.jobs.official_fetch import ALLOWED_HOSTS
    host = next(iter(ALLOWED_HOSTS))
    with pytest.raises(OfficialSourcePolicyError):
        require_official_https(f'http://{host}/notice')


def test_unknown_host_is_not_authoritative():
    assert is_autonomous_publication_allowed('https://example.invalid/notice') is False
