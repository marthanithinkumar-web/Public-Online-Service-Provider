from app.jobs.official_fetch import validate_official_url
from app.jobs.rrb_extra import parse_rrb_regional
from app.jobs.sources import SOURCE_BY_KEY


def test_regional_rrb_sources_are_registered():
    assert SOURCE_BY_KEY['rrb_secunderabad'].listing_url == 'https://rrbsecunderabad.gov.in/employment-notice/'
    assert SOURCE_BY_KEY['rrb_chennai'].listing_url == 'https://www.rrbchennai.gov.in/'


def test_regional_rrb_official_hosts_are_allowlisted():
    assert validate_official_url('https://rrbsecunderabad.gov.in/employment-notice/')
    assert validate_official_url('https://www.rrbchennai.gov.in/')


def test_regional_rrb_parser_keeps_initial_cen_and_ignores_updates():
    html = '''
      <section>
        <h4>CEN 04/2099 (JE & DMS) - Detailed Centralized Employment Notification for recruitment to the posts of Junior Engineer and Depot Material Superintendent</h4>
        <p>Date : 13/08/2099</p>
        <a href="/downloads/cen-04-2099.pdf">English notification</a>
      </section>
      <section>
        <h4>CEN 04/2099 - Result and document verification schedule</h4>
        <a href="/downloads/result.pdf">Result</a>
      </section>
    '''
    items = parse_rrb_regional(html, 'https://rrbsecunderabad.gov.in/employment-notice/')
    assert len(items) == 1
    assert items[0].external_id == 'secunderabad-CEN04-2099'
    assert items[0].organization == 'Railway Recruitment Board (RRB) Secunderabad'
    assert items[0].official_notice_url == 'https://rrbsecunderabad.gov.in/downloads/cen-04-2099.pdf'
