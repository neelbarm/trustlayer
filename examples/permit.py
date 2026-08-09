"""A worked example: twelve fields extracted from a construction permit.

The permit_fee field is the interesting one. It carries 0.94 confidence and is
wrong, because the extraction took the first line item instead of the total.
Run this with and without verification to see the difference that makes.
"""

from trustlayer import Field, Policy, Verification, decide_all, render, worth_of_verification

V, M, N = Verification.VERIFIED, Verification.MISMATCH, Verification.NOT_FOUND

FIELDS = [
    Field("permit_number", "BLD-2024-041877", 0.99, verification=V),
    Field("issue_date", "2024-03-14", 0.98, verification=V),
    Field("site_address", "1450 El Camino Real, San Mateo, CA", 0.98, verification=V),
    Field("issuing_authority", "City of San Mateo, DPW", 0.98, verification=V),
    Field("permit_type", "Wireless Comm. Facility (Small Cell)", 0.97, verification=V),
    Field("parcel_id", "034-172-090", 0.97, verification=V),
    Field("applicant", "Northbay Wireless Infrastructure, LLC", 0.95, verification=V),
    # Confident and wrong: this is the plan-review line item, not the total paid.
    Field("permit_fee", "$1,240.00", 0.94, verification=M),
    Field("scope_of_work", "Small-cell node on wood pole", 0.93, verification=V),
    Field("conditions", "180-day validity, final electrical", 0.91, verification=V),
    # Never stated outright, inferred from a condition clause.
    Field("expiration_date", "2024-09-10", 0.55, verification=N),
    # Handwritten and only partly legible.
    Field("contractor", "Meridian Tower Svcs", 0.38, verification=N),
]

POLICY = Policy(
    standard_bar=0.85,
    high_stakes_bar=0.95,
    high_stakes=frozenset({"permit_number", "issue_date", "expiration_date", "site_address"}),
)

if __name__ == "__main__":
    print(render(decide_all(FIELDS, POLICY), title="verification ON"))
    print(render(decide_all(FIELDS, POLICY, verified=False), title="verification OFF"))
    print(f"  the verification pass keeps {worth_of_verification(FIELDS, POLICY)} "
          f"wrong value(s) out of the record\n")
