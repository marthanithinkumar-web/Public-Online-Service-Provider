from marshmallow import Schema, fields, validate


class OrderCreateSchema(Schema):
    contact_method = fields.Str(allow_none=True)
    service_id = fields.Int(required=True)
    application_data = fields.Dict(required=True, allow_none=False)


class OrderSchema(Schema):
    id = fields.Int(dump_only=True)
    order_code = fields.Str(dump_only=True)
    client_name = fields.Str()
    phone = fields.Str()
    email = fields.Str(allow_none=True)
    contact_method = fields.Str(allow_none=True)
    service = fields.Function(lambda order: order.service.name if order.service else None)
    service_id = fields.Int()
    user_id = fields.Int(dump_only=True)
    fee_inr = fields.Float()
    official_fee_inr = fields.Float(allow_none=True)
    official_fee_status = fields.Str()
    total_fee_inr = fields.Float(allow_none=True)
    status = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    application_data = fields.Dict()
