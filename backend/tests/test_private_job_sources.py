from app.jobs.official_fetch import validate_official_url
from app.jobs.private_sources import parse_private_careers
from app.jobs.sources import SOURCE_BY_KEY


def test_private_sources_are_registered_and_official():
    expected = {
        'wipro_careers': 'https://careers.wipro.com/viewalljobs/',
        'infosys_careers': 'https://digitalcareers.infosys.com/infosys/global-careers?location=India',
        'accenture_careers': 'https://www.accenture.com/in-en/careers/jobsearch',
    }
    for key, url in expected.items():
        assert SOURCE_BY_KEY[key].listing_url == url
        assert validate_official_url(url) == url


def test_wipro_parser_marks_jobs_private():
    html = '<a href="/job/Hyderabad-Cloud-Engineer-500123/">Cloud Engineer</a>'
    items = parse_private_careers(html, 'https://careers.wipro.com/viewalljobs/')
    assert len(items) == 1
    assert items[0].organization == 'Wipro'
    assert items[0].job_type == 'private'
    assert items[0].official_notice_url.startswith('https://careers.wipro.com/job/')


def test_infosys_parser_keeps_official_role_links_only():
    html = '''
    <a href="/infosys/global-careers/jobdetails/153105BR">Principal Consultant</a>
    <a href="/infosys/global-careers">Search jobs</a>
    '''
    items = parse_private_careers(html, 'https://digitalcareers.infosys.com/infosys/global-careers?location=India')
    assert len(items) == 1
    assert items[0].organization == 'Infosys'
    assert items[0].job_type == 'private'


def test_accenture_parser_keeps_jobdetails_links():
    html = '''
    <a href="jobdetails?id=ATCI-12345_en">Application Developer</a>
    <a href="/in-en/careers/jobsearch">Search Jobs</a>
    '''
    items = parse_private_careers(html, 'https://www.accenture.com/in-en/careers/jobsearch')
    assert len(items) == 1
    assert items[0].organization == 'Accenture'
    assert items[0].job_type == 'private'
    assert 'jobdetails?id=ATCI-12345_en' in items[0].official_notice_url
