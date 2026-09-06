"""Administrative Flask CLI commands."""

import json

import click

from .utils.attachment_retention import purge_historical_client_attachments


def register_cli(app):
    @app.cli.command('purge-closed-client-documents')
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
    def purge_closed_client_documents(apply, limit):
        """Find or purge legacy client uploads attached to closed requests."""
        result = purge_historical_client_attachments(apply=apply, limit=limit)
        click.echo(json.dumps(result, sort_keys=True))
        if result['failed_attachments']:
            raise click.ClickException(
                f"{result['failed_attachments']} attachment(s) could not be purged; rerun after resolving storage access."
            )
