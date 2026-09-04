import pytest

from app.jobs.official_fetch import validate_official_url


def test_current_india_post_gds_application_host_is_approved():
    assert validate_official_url('https://app.indiapost.gov.in/') == 'https://app.indiapost.gov.in/'


def test_unapproved_lookalike_india_post_host_is_rejected():
    with pytest.raises(ValueError):
        validate_official_url('https://app.indiapost.gov.in.evil.example/')
