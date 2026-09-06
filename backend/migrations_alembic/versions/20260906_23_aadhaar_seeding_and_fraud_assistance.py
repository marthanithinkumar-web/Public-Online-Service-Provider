"""add Aadhaar seeding and online fraud complaint assistance

Revision ID: 20260906_23
Revises: 20260906_22
"""
from alembic import op
import sqlalchemy as sa

revision='20260906_23'
down_revision='20260906_22'
branch_labels=None
depends_on=None

SERVICES=(
 ('Aadhaar - Bank Account Seeding / DBT Assistance','Guidance for linking Aadhaar with a bank account and requesting DBT/NPCI mapper seeding through the client bank. The bank performs the linking/seeding; clients complete OTP, biometric, bank login and final authorization only with the bank or official service.','aadhaar seeding,aadhar seeding,bank aadhaar link,dbt,npcI mapper,bank seeding,benefit transfer',10.0),
 ('Online Fraud Complaint Raise Assistance','Guidance for preparing and submitting an online cyber/fraud complaint through the official National Cyber Crime Reporting Portal. For ongoing or recent financial fraud, clients should immediately call 1930 and report through the official portal before using assistance. We never request OTPs, PINs, passwords or banking credentials.','online fraud complaint,cyber crime,cybercrime,1930,financial fraud,upi fraud,bank fraud,online scam,complaint assistance',10.0),
)

def upgrade():
 bind=op.get_bind()
 category=bind.execute(sa.text("SELECT id FROM categories WHERE name='Other Online Public Services' LIMIT 1")).scalar()
 if category is None:
  bind.execute(sa.text("INSERT INTO categories (name) VALUES ('Other Online Public Services')"))
  category=bind.execute(sa.text("SELECT id FROM categories WHERE name='Other Online Public Services' LIMIT 1")).scalar()
 for name,description,keywords,price in SERVICES:
  exists=bind.execute(sa.text('SELECT id FROM services WHERE name=:name LIMIT 1'),{'name':name}).scalar()
  values={'name':name,'description':description,'keywords':keywords,'price':price,'category':category}
  if exists:
   bind.execute(sa.text("UPDATE services SET description=:description, keywords=:keywords, price_inr=:price, official_fee_inr=0, official_fee_status='none', category_id=:category, is_active=true WHERE name=:name"),values)
  else:
   bind.execute(sa.text("INSERT INTO services (name,description,keywords,price_inr,official_fee_inr,official_fee_status,category_id,is_active) VALUES (:name,:description,:keywords,:price,0,'none',:category,true)"),values)

def downgrade():
 bind=op.get_bind()
 for name,_,_,_ in SERVICES:
  bind.execute(sa.text('DELETE FROM services WHERE name=:name'),{'name':name})
