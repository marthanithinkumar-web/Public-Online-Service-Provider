"""Administrative maintenance commands.

Run from the backend directory with::

    python -m app.cli
    python -m app.cli --apply

The command is intentionally dry-run by default.
"""

import json

import click

from .utils.attachment_retention import purge_historical_client_attachments


@click.command()
@click.option(
    '--apply',
    is_flag=True,
    help='Permanently delete matched client documents. Without this flag the command is read-only.',
)
@click.option(
    '--limit',
    type=click.IntRange(min=1),
    default=None,
    help='Process at most this many attachments in one run.',
)
def main(apply, limit):
    """Find or purge legacy client uploads attached to closed requests."""
    from .main import create_app

    app = create_app()
    with app.app_context():
        result = purge_historical_client_attachments(apply=apply, limit=limit)

    click.echo(json.dumps(result, sort_keys=True))
    if result['failed_attachments']:
        raise click.ClickException(
            f"{result['failed_attachments']} attachment(s) could not be purged; rerun after resolving storage access."
        )


if __name__ == '__main__':
    main()
