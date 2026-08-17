from marshmallow import Schema, fields


class AttachmentSchema(Schema):
    id = fields.Int(dump_only=True)
    order_id = fields.Int()
    filename = fields.Str()
    stored_path = fields.Str()
    uploaded_by = fields.Int()
    created_at = fields.DateTime()
