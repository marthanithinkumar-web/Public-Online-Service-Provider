from marshmallow import Schema, fields, validate


class OrderCreateSchema(Schema):
    client_name = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    phone = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(allow_none=True)
    contact_method = fields.Str(allow_none=True)
    service_id = fields.Int(required=True)
    description = fields.Str(allow_none=True)


class OrderSchema(Schema):
    id = fields.Int(dump_only=True)
    order_code = fields.Str(dump_only=True)
    client_name = fields.Str()
    phone = fields.Str()
    email = fields.Str()
    service = fields.Str()
    user_id = fields.Int(dump_only=True)
    fee_inr = fields.Float()
    status = fields.Str()
    created_at = fields.DateTime()
