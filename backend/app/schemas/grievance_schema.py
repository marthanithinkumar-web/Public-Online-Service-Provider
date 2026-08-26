from marshmallow import Schema, fields, validate


class GrievanceCreateSchema(Schema):
    order_id = fields.Int(required=False, allow_none=True)
    description = fields.Str(required=True, validate=validate.Length(min=5, max=4000))


class GrievanceSchema(Schema):
    id = fields.Int(dump_only=True)
    grievance_code = fields.Str()
    user_id = fields.Int(load_only=True)
    order_id = fields.Int()
    client_name = fields.Str()
    phone = fields.Str()
    email = fields.Str()
    description = fields.Str()
    status = fields.Str()
    admin_response = fields.Str(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
