from app.jobs.official_fetch import validate_official_url
from app.jobs.rrb_central import parse_rrcb
from app.jobs.sources import SOURCE_BY_KEY


def test_rrb_source_uses_central_rrcb():
    source = SOURCE_BY_KEY['rrb']
    assert source.listing_url == 'https://www.rrcb.gov.in/Employment_notices.html'
    assert validate_official_url(source.listing_url) == source.listing_url


def test_rrcb_parser_reads_central_cen_table():
    html = '''<table><tr><th>Serial No</th><th>Employment Notification</th><th>Updates</th></tr>
    <tr><td>1</td><td>CEN 02/2099 (Technicians)</td><td><a href="/notice-02-2099.html">Click here</a></td></tr>
    <tr><td>2</td><td>CEN 01/2099 (ALP)</td><td><a href="/notice-01-2099.html">Click here</a></td></tr></table>'''
    items = parse_rrcb(html, 'https://www.rrcb.gov.in/Employment_notices.html')
    assert len(items) == 2
    assert items[0].organization.startswith('Railway Recruitment Control Board')
    assert items[0].official_notice_url == 'https://www.rrcb.gov.in/notice-02-2099.html'
