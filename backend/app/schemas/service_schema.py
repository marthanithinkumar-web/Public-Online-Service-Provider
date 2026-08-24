from marshmallow import Schema, fields, validate


class ServiceSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=300))
    description = fields.Str(allow_none=True)
    price_inr = fields.Float(load_default=0.0)
    keywords = fields.Str(allow_none=True)
    category_id = fields.Int(allow_none=True)
    category = fields.Str(dump_only=True)
