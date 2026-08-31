from app.utils import s3


class FakeS3Client:
    def __init__(self, versions=None):
        self.versions = versions or {}
        self.deleted = []

    def list_object_versions(self, **kwargs):
        assert kwargs == {'Bucket': 'private-bucket', 'Prefix': 'attachments/document.pdf'}
        return self.versions

    def delete_object(self, **kwargs):
        self.deleted.append(kwargs)


def test_delete_stored_file_permanently_removes_matching_versions(monkeypatch):
    client = FakeS3Client({
        'Versions': [
            {'Key': 'attachments/document.pdf', 'VersionId': 'version-1'},
            {'Key': 'attachments/document.pdf.backup', 'VersionId': 'unrelated'},
        ],
        'DeleteMarkers': [{'Key': 'attachments/document.pdf', 'VersionId': 'marker-1'}],
    })
    monkeypatch.setattr(s3, 's3_client', lambda: client)

    s3.delete_stored_file('s3://private-bucket/attachments/document.pdf')

    assert client.deleted == [
        {'Bucket': 'private-bucket', 'Key': 'attachments/document.pdf', 'VersionId': 'version-1'},
        {'Bucket': 'private-bucket', 'Key': 'attachments/document.pdf', 'VersionId': 'marker-1'},
    ]


def test_delete_stored_file_uses_idempotent_delete_when_no_version_is_listed(monkeypatch):
    client = FakeS3Client()
    monkeypatch.setattr(s3, 's3_client', lambda: client)

    s3.delete_stored_file('s3://private-bucket/attachments/document.pdf')

    assert client.deleted == [{'Bucket': 'private-bucket', 'Key': 'attachments/document.pdf'}]


def test_delete_stored_file_removes_local_fallback(tmp_path):
    document = tmp_path / 'document.pdf'
    document.write_bytes(b'%PDF-1.4\n%%EOF')

    s3.delete_stored_file(str(document))

    assert not document.exists()
