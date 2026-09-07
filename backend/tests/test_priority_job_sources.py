from app.jobs import sources
from app.jobs.priority_sources import parse_rbi


def test_employment_news_all_jobs_is_removed_and_priority_sources_are_registered():
    keys = [source.key for source in sources.SOURCE_DEFINITIONS]

    assert 'employment_news' not in keys
    for key in ('ssc', 'rrb', 'upsc', 'rbi', 'sbi', 'nvs', 'sainik_schools', 'kvs', 'sebi', 'ibps', 'drdo_rac'):
        assert key in keys

    assert keys.index('rbi') < keys.index('ssc')
    assert keys.index('sbi') < keys.index('ssc')
    assert all('employmentnews.gov.in/NewEmp/AllJobs.aspx' not in source.listing_url for source in sources.SOURCE_DEFINITIONS)


def test_priority_parser_keeps_recruitment_notice_and_excludes_results():
    html = '''
    <ul>
      <li><a href="/Scripts/bs_viewcontent.aspx?Id=5001">Direct Recruitment for Officers Grade B 2026 - Last date 30 September 2026</a></li>
      <li><a href="/Scripts/bs_viewcontent.aspx?Id=5002">Final Result - Recruitment for Officers Grade B 2026</a></li>
      <li><a href="/Scripts/CallLetters.aspx">Call Letter for Recruitment Examination</a></li>
    </ul>
    '''

    items = parse_rbi(html, 'https://opportunities.rbi.org.in/Scripts/Vacancies.aspx')

    assert len(items) == 1
    assert items[0].organization == 'Reserve Bank of India (RBI)'
    assert items[0].deadline.isoformat() == '2026-09-30'
    assert items[0].official_notice_url == 'https://opportunities.rbi.org.in/Scripts/bs_viewcontent.aspx?Id=5001'
