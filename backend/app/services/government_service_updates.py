"""Verified government-service update metadata.

This module records high-confidence, first-party service changes that are useful to
surface in the catalogue and in future automated refresh checks. It intentionally
stores no credentials and does not call third-party APIs at import time.
"""

GOVERNMENT_SERVICE_UPDATES = {
    "aadhaar_mobile_number_update": {
        "name": "Aadhaar - Mobile Number Update Assistance",
        "status": "online-supported",
        "official_source": "UIDAI Aadhaar app",
        "notes": (
            "UIDAI states that mobile-number update is supported directly through the Aadhaar app. "
            "Cases where the resident cannot access the old registered number or has never registered "
            "a mobile number may still require an Aadhaar Seva Kendra/authorised centre."
        ),
    },
    "aadhaar_address_update": {
        "name": "Aadhaar - Address Update Assistance",
        "status": "online-supported",
        "official_source": "UIDAI Aadhaar app / myAadhaar",
        "notes": "Address update is available through UIDAI online channels for eligible residents.",
    },
    "aadhaar_email_update": {
        "name": "Aadhaar - Email Update Assistance",
        "status": "online-supported",
        "official_source": "UIDAI Aadhaar mobile application",
        "notes": (
            "UIDAI's June 2026 office memorandum confirms email-address update through the Aadhaar "
            "mobile application and waives the service charge from 1 July 2026 through 31 December 2026."
        ),
    },
    "aadhaar_document_update": {
        "name": "Aadhaar - Document Update Assistance",
        "status": "online-supported",
        "official_source": "UIDAI myAadhaar",
        "notes": "Document Update is available through myAadhaar; UIDAI extended the online fee relaxation through 14 June 2027.",
    },
    "aadhaar_pvc": {
        "name": "Aadhaar PVC Card Order",
        "status": "online",
        "official_source": "UIDAI",
        "notes": "UIDAI's online PVC-card service costs ₹75 inclusive of GST and Speed Post charges from 1 January 2026.",
    },
    "pan_aadhaar_link": {
        "name": "PAN - Aadhaar Linking Assistance",
        "status": "online",
        "official_source": "Income Tax e-Filing portal",
        "notes": "The Link Aadhaar service is available online on the Income Tax e-Filing portal; exemptions and any applicable late-linking fee depend on the taxpayer's case.",
    },
    "passport_fee_refresh_2026": {
        "name": "Passport - New Application",
        "status": "official-fee-changed",
        "official_source": "Passport Seva",
        "notes": "Passport Seva states that passport application fees were revised with effect from 1 July 2026; clients should be shown the current official fee before payment.",
    },
}
