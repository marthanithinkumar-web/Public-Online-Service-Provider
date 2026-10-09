import pytest

from app.ai_tools.official_source_policy import (
    OfficialSourcePolicyError,
    is_autonomous_publication_allowed,
    require_official_https,
)


def test_approved_official_source_is_allowed():
    assert is_autonomous_publication_allowed('https://ssc.gov.in/notice') is True


def test_unapproved_aggregator_is_rejected():
    assert is_autonomous_publication_allowed('https://example.com/job') is False


def test_http_source_is_rejected():
    with pytest.raises(OfficialSourcePolicyError):
        require_official_https('http://ssc.gov.in/notice')


def test_credentials_in_url_are_rejected():
    with pytest.raises(OfficialSourcePolicyError):
        require_official_https('https://user:pass@ssc.gov.in/notice')
