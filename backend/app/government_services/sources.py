"""First-party portals used to discover and verify government-service changes.

This is deliberately a registry of government-owned/service-provider portals, not
third-party blogs. New departments can be added without changing the importer.
"""

SOURCES = (
    {'key': 'india', 'name': 'National Portal of India', 'url': 'https://www.india.gov.in/'},
    {'key': 'uidai', 'name': 'UIDAI', 'url': 'https://www.uidai.gov.in/en/my-aadhaar'},
    {'key': 'income_tax', 'name': 'Income Tax Department', 'url': 'https://www.incometax.gov.in/iec/foportal/'},
    {'key': 'passport', 'name': 'Passport Seva', 'url': 'https://www.passportindia.gov.in/psp/'},
    {'key': 'voters', 'name': 'Election Commission Voters Service Portal', 'url': 'https://voters.eci.gov.in/'},
    {'key': 'parivahan', 'name': 'Parivahan Sewa', 'url': 'https://parivahan.gov.in/parivahan/'},
    {'key': 'digilocker', 'name': 'DigiLocker', 'url': 'https://www.digilocker.gov.in/'},
    {'key': 'umang', 'name': 'UMANG', 'url': 'https://web.umang.gov.in/'},
    {'key': 'epfo', 'name': 'Employees Provident Fund Organisation', 'url': 'https://www.epfindia.gov.in/'},
    {'key': 'eshram', 'name': 'e-Shram', 'url': 'https://eshram.gov.in/'},
    {'key': 'ncs', 'name': 'National Career Service', 'url': 'https://www.ncs.gov.in/'},
    {'key': 'pmkisan', 'name': 'PM-KISAN', 'url': 'https://pmkisan.gov.in/'},
    {'key': 'pmjay', 'name': 'Ayushman Bharat PM-JAY', 'url': 'https://pmjay.gov.in/'},
    {'key': 'udyam', 'name': 'Udyam Registration', 'url': 'https://udyamregistration.gov.in/'},
    {'key': 'gst', 'name': 'GST Portal', 'url': 'https://www.gst.gov.in/'},
    {'key': 'fssai', 'name': 'FSSAI', 'url': 'https://www.fssai.gov.in/'},
    {'key': 'nsp', 'name': 'National Scholarship Portal', 'url': 'https://scholarships.gov.in/'},
    {'key': 'meeseva_tg', 'name': 'Telangana MeeSeva', 'url': 'https://ts.meeseva.telangana.gov.in/'},
    {'key': 'ap_seva', 'name': 'Andhra Pradesh GSWS', 'url': 'https://vswsonline.ap.gov.in/'},
)

SERVICE_WORDS = (
    'apply', 'application', 'register', 'registration', 'update', 'correction',
    'download', 'certificate', 'licence', 'license', 'card', 'pension', 'scheme',
    'benefit', 'status', 'link', 'renewal', 'reissue', 'claim', 'appointment',
    'admission', 'scholarship', 'service', 'portal', 'payment', 'verification',
)
