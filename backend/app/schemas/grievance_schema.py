from marshmallow import Schema, fields, validate


class GrievanceCreateSchema(Schema):
    order_id = fields.Int(allow_none=True)
    client_name = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    phone = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(allow_none=True)
    description = fields.Str(allow_none=True)


class GrievanceSchema(Schema):
    id = fields.Int(dump_only=True)
    grievance_code = fields.Str()
    order_id = fields.Int()
    client_name = fields.Str()
    phone = fields.Str()
    email = fields.Str()
    description = fields.Str()
    status = fields.Str()
    created_at = fields.DateTime()
