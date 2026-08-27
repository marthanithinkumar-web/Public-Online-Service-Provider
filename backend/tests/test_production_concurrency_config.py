from app.main import database_engine_options


def test_postgres_pool_settings_are_configurable(monkeypatch):
    monkeypatch.setenv('DB_POOL_SIZE','7')
    monkeypatch.setenv('DB_MAX_OVERFLOW','3')
    monkeypatch.setenv('DB_POOL_TIMEOUT','15')
    monkeypatch.setenv('DB_CONNECT_TIMEOUT','8')
    monkeypatch.setenv('DB_STATEMENT_TIMEOUT_MS','12000')

    options=database_engine_options('postgresql://example/database')

    assert options['pool_pre_ping'] is True
    assert options['pool_size'] == 7
    assert options['max_overflow'] == 3
    assert options['pool_timeout'] == 15
    assert options['connect_args'] == {
        'connect_timeout': 8,
        'options': '-c statement_timeout=12000',
    }


def test_sqlite_does_not_receive_postgres_pool_limits():
    options=database_engine_options('sqlite:///test.db')

    assert 'pool_size' not in options
    assert 'max_overflow' not in options
    assert 'connect_args' not in options
