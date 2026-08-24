from marshmallow import Schema, fields, validate


class ReviewCreateSchema(Schema):
    order_id = fields.Int(required=True)
    rating = fields.Int(required=True, validate=validate.Range(min=1, max=5))
    comment = fields.Str(allow_none=True, validate=validate.Length(max=2000))


class ReviewSchema(Schema):
    id = fields.Int(dump_only=True)
    order_id = fields.Int()
    rating = fields.Int()
    comment = fields.Str()
    client_name = fields.Str()
    is_public = fields.Bool()
    created_at = fields.DateTime()
