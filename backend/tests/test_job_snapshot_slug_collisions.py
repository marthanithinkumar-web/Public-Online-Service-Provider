from app.jobs.snapshot import _ensure_unique_slugs


def test_duplicate_legacy_slug_keeps_first_url_and_repairs_later_collision():
    jobs = [
        {
            'slug': 'apprenticeship-training-in-ntpc-corporate-centre',
            'title': 'Apprenticeship Training in NTPC Corporate Centre',
            'organization': 'NTPC',
            'content_hash': 'a' * 64,
        },
        {
            'slug': 'apprenticeship-training-in-ntpc-corporate-centre',
            'title': 'Apprenticeship Training in NTPC Corporate Centre',
            'organization': 'NTPC Corporate Centre',
            'content_hash': 'b' * 64,
        },
    ]

    repaired = _ensure_unique_slugs(jobs)

    assert repaired[0]['slug'] == 'apprenticeship-training-in-ntpc-corporate-centre'
    assert repaired[1]['slug'] != repaired[0]['slug']
    assert repaired[1]['slug'].endswith('-bbbbbbbbbb')
    assert len(repaired[1]['slug']) <= 250


def test_unique_existing_slugs_are_left_unchanged():
    jobs = [
        {'slug': 'one-job', 'title': 'One Job', 'organization': 'Org A', 'content_hash': '1' * 64},
        {'slug': 'two-job', 'title': 'Two Job', 'organization': 'Org B', 'content_hash': '2' * 64},
    ]

    repaired = _ensure_unique_slugs(jobs)

    assert [job['slug'] for job in repaired] == ['one-job', 'two-job']


def test_missing_slug_gets_a_deterministic_public_slug():
    original = {
        'title': 'Graduate Apprentice',
        'organization': 'Example Corporation',
        'content_hash': 'c' * 64,
    }

    first = _ensure_unique_slugs([dict(original)])[0]['slug']
    second = _ensure_unique_slugs([dict(original)])[0]['slug']

    assert first == second
    assert first.endswith('-cccccccccc')
