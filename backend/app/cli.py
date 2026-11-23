"""Administrative maintenance commands.

Run from the backend directory with::

    python -m app.cli
    python -m app.cli --apply

The command is intentionally dry-run by default.
"""

import json

import click

from .utils.attachment_retention import purge_historical_client_attachments
from .utils.whatsapp_retention import purge_whatsapp_messages


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
    help='Process at most this many retention records in one run.',
)
@click.option(
    '--whatsapp-messages',
    is_flag=True,
    help='Preview or purge expired WhatsApp message rows instead of client attachments.',
)
def main(apply, limit, whatsapp_messages):
    """Run one explicit, dry-run-by-default retention maintenance action."""
    from .main import create_app

    app = create_app()
    with app.app_context():
        if whatsapp_messages:
            result = purge_whatsapp_messages(apply=apply, limit=limit)
        else:
            result = purge_historical_client_attachments(apply=apply, limit=limit)

    click.echo(json.dumps(result, sort_keys=True))
    failed_key = 'failed_messages' if whatsapp_messages else 'failed_attachments'
    if result[failed_key]:
        raise click.ClickException(
            f"{result[failed_key]} retention item(s) could not be purged; rerun after resolving the failure."
        )


if __name__ == '__main__':
    main()
