-- Seed basic categories and services

INSERT INTO categories (name) VALUES ('Certificates') ON CONFLICT DO NOTHING;
INSERT INTO categories (name) VALUES ('Government Jobs') ON CONFLICT DO NOTHING;
INSERT INTO categories (name) VALUES ('MeeSeva / Public Services') ON CONFLICT DO NOTHING;
INSERT INTO categories (name) VALUES ('Scholarships') ON CONFLICT DO NOTHING;

-- Example services
INSERT INTO services (name, description, price_inr, keywords, category_id)
VALUES
('Residence Certificate', 'Assistance to apply for residence/domicile certificate', 30.0, 'residence,domicile,address,certificate', 1),
('Ration Card Services', 'Help with Ration Card related applications', 50.0, 'ration,card,food,subsidy', 1),
('Government Job Application', 'Assistance to apply for government job openings', 100.0, 'job,application,recruitment', 2)
ON CONFLICT DO NOTHING;
