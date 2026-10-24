import pytest

from app.jobs.official_fetch import validate_official_url


def test_current_india_post_gds_application_host_is_approved():
    assert validate_official_url('https://app.indiapost.gov.in/') == 'https://app.indiapost.gov.in/'


def test_unapproved_lookalike_india_post_host_is_rejected():
    with pytest.raises(ValueError):
        validate_official_url('https://app.indiapost.gov.in.evil.example/')


def test_current_sbi_careers_host_is_approved():
    assert validate_official_url('https://sbi.bank.in/web/careers/current-openings') == 'https://sbi.bank.in/web/careers/current-openings'


def test_unapproved_sbi_lookalike_host_is_rejected():
    with pytest.raises(ValueError):
        validate_official_url('https://sbi.bank.in.evil.example/web/careers/current-openings')
