"""
generate_sample_docs.py
───────────────────────
Generates realistic sample regulatory and internal policy documents
as plain text files. Run this once to populate the documents/ folder.

In a real deployment these would be actual PDFs from:
  - FATF (fatf-gafi.org)
  - Basel Committee (bis.org)
  - Internal compliance team

For demo purposes we create realistic synthetic versions that mirror
the structure and language of real financial regulatory documents.
"""

import os

# ── Regulatory Documents ─────────────────────────────────────────────────────

FATF_AML = """
FINANCIAL ACTION TASK FORCE (FATF)
RECOMMENDATIONS ON ANTI-MONEY LAUNDERING AND COUNTER-TERRORIST FINANCING
Revised Edition

RECOMMENDATION 10: CUSTOMER DUE DILIGENCE

Financial institutions should be prohibited from keeping anonymous accounts or accounts
in obviously fictitious names. Financial institutions should be required to undertake
customer due diligence (CDD) measures when:

(i)   establishing business relations;
(ii)  carrying out occasional transactions above the applicable designated threshold
      (USD/EUR 15,000);
(iii) there is a suspicion of money laundering or terrorist financing; or
(iv)  the financial institution has doubts about the veracity or adequacy of previously
      obtained customer identification data.

The CDD measures to be taken are as follows:
a) Identifying the customer and verifying that customer's identity using reliable,
   independent source documents, data or information.
b) Identifying the beneficial owner, and taking reasonable measures to verify the
   identity of the beneficial owner, such that the financial institution is satisfied
   that it knows who the beneficial owner is.
c) Understanding and, as appropriate, obtaining information on the purpose and
   intended nature of the business relationship.
d) Conducting ongoing due diligence on the business relationship and scrutiny of
   transactions undertaken throughout the course of that relationship to ensure that
   the transactions being conducted are consistent with the institution's knowledge
   of the customer, their business and risk profile, including, where necessary,
   the source of funds.

ONGOING MONITORING REQUIREMENTS:
Financial institutions must conduct ongoing monitoring of ALL business relationships
regardless of transaction amount. This includes periodic review of customer risk
profiles, transaction pattern analysis, and enhanced scrutiny of high-risk customers.
No threshold exemption applies to ongoing monitoring obligations.

RECOMMENDATION 11: RECORD KEEPING

Financial institutions should be required to maintain, for at least five years, all
necessary records on transactions, both domestic and international, to enable them
to comply swiftly with information requests from the competent authorities.

Transaction records must include:
- The name and address of the customer
- The nature and date of the transaction
- The type and amount of currency involved
- The type and identifying number of any account involved
- The name and address of the counterpart institution

RECOMMENDATION 20: REPORTING OF SUSPICIOUS TRANSACTIONS

If a financial institution suspects or has reasonable grounds to suspect that funds
are the proceeds of a criminal activity, or are related to terrorist financing, it
should be required, directly by law or regulation, to report promptly its suspicions
to the Financial Intelligence Unit (FIU).

Reporting threshold: ANY suspicious activity regardless of amount.
Tipping off prohibition: Institutions and their staff are prohibited from disclosing
that a suspicious transaction report (STR) has been filed.

RECOMMENDATION 26: REGULATION AND SUPERVISION OF FINANCIAL INSTITUTIONS

Financial institutions should be subject to adequate regulation and supervision and
are effectively implementing the FATF Recommendations. The supervisory authority
should have adequate powers to supervise or monitor, and ensure compliance by,
financial institutions with requirements to combat money laundering and terrorist
financing including the authority to conduct inspections.

RISK-BASED APPROACH:
Institutions must apply a risk-based approach (RBA) to AML/CFT measures, allocating
resources according to identified risks. Higher-risk customers (PEPs, non-resident
customers, cash-intensive businesses) require Enhanced Due Diligence (EDD).
"""

BASEL_CAPITAL = """
BASEL COMMITTEE ON BANKING SUPERVISION
BASEL III: A GLOBAL REGULATORY FRAMEWORK FOR MORE RESILIENT BANKS
Bank for International Settlements

PART 1: MINIMUM CAPITAL REQUIREMENTS

1.1 COMPOSITION OF CAPITAL

Regulatory capital consists of three tiers:

TIER 1 CAPITAL (Going-concern capital):
Common Equity Tier 1 (CET1):
  - Common shares issued by the bank
  - Stock surplus resulting from the issue of CET1 instruments
  - Retained earnings
  - Accumulated other comprehensive income
  Minimum CET1 ratio: 4.5% of risk-weighted assets (RWA)

Additional Tier 1 (AT1):
  - Instruments issued by the bank that meet AT1 criteria
  - Stock surplus resulting from the issue of AT1 instruments
  Minimum Tier 1 ratio: 6.0% of RWA

TIER 2 CAPITAL (Gone-concern capital):
  - Instruments issued by the bank that meet Tier 2 criteria
  - General provisions/general loan-loss reserves
  Minimum Total Capital ratio: 8.0% of RWA

1.2 CAPITAL CONSERVATION BUFFER

Banks must maintain a capital conservation buffer of 2.5% of total RWA,
comprised of CET1 capital. This buffer exists to absorb losses during
periods of financial and economic stress. When the buffer is drawn down,
automatic constraints on earnings distributions are applied:

Buffer level (CET1)     | Minimum conservation ratio
4.5% - 5.125%           | 100% (no distribution allowed)
5.125% - 5.75%          | 80%
5.75% - 6.375%          | 60%
6.375% - 7.0%           | 40%
Above 7.0%              | 0% (no constraint)

1.3 COUNTERCYCLICAL CAPITAL BUFFER

Jurisdictional authorities may impose an additional countercyclical buffer
of 0% to 2.5% of RWA during periods of excessive credit growth.

1.4 LEVERAGE RATIO

A non-risk-based leverage ratio serves as a backstop to the risk-based
capital requirements. Minimum Tier 1 leverage ratio: 3.0%.

PART 2: LIQUIDITY REQUIREMENTS

2.1 LIQUIDITY COVERAGE RATIO (LCR)

Banks must maintain adequate high-quality liquid assets (HQLA) to survive
a significant stress scenario lasting 30 calendar days.

LCR = Stock of HQLA / Total net cash outflows over 30 days >= 100%

HQLA includes:
  Level 1: Cash, central bank reserves, zero risk-weight sovereign debt (no haircut)
  Level 2A: 20% haircut — certain sovereign/central bank debt, covered bonds
  Level 2B: 25-50% haircut — RMBS, corporate bonds, equities

2.2 NET STABLE FUNDING RATIO (NSFR)

Banks must maintain a stable funding profile in relation to the composition
of their assets and off-balance sheet activities.

NSFR = Available Stable Funding / Required Stable Funding >= 100%

PART 3: REPORTING REQUIREMENTS

Banks must report capital ratios to supervisory authorities quarterly.
Any breach of minimum capital requirements must be reported within 24 hours.
Recovery plans must be updated annually and submitted to regulators.
"""

KYC_GUIDELINES = """
KNOW YOUR CUSTOMER (KYC) COMPLIANCE GUIDELINES
Regulatory Guidance for Financial Institutions and Fintech Companies

SECTION 1: CUSTOMER IDENTIFICATION PROGRAM (CIP)

1.1 IDENTITY VERIFICATION REQUIREMENTS

All financial institutions and fintech companies onboarding customers must:

For Individual Customers:
  - Full legal name (must match government-issued ID)
  - Date of birth
  - Residential address (no P.O. boxes for primary address)
  - Government-issued identification number (SSN, passport number, or equivalent)
  - Verification must be completed BEFORE account opening or first transaction

For Corporate Customers:
  - Legal entity name and type
  - Principal place of business
  - Employer Identification Number (EIN) or equivalent
  - Beneficial ownership identification (all individuals owning 25% or more)
  - Identification of control person (single individual with significant responsibility)

1.2 DOCUMENT VERIFICATION

Acceptable identity documents:
  Primary: Government-issued photo ID (passport, driver's license, national ID)
  Secondary: Utility bill, bank statement (not older than 3 months)

Digital verification: e-KYC acceptable when using:
  - Biometric verification with liveness detection
  - Document authenticity verification (NFC chip reading preferred)
  - Cross-reference against government databases where available

1.3 RISK CATEGORIZATION

Upon onboarding, customers must be assigned a risk rating:

LOW RISK:
  - Domestic residents with stable employment
  - Established businesses in low-risk sectors
  - Standard monitoring: annual review

MEDIUM RISK:
  - Non-resident customers
  - Businesses in moderate-risk sectors (real estate, car dealers)
  - Enhanced monitoring: semi-annual review

HIGH RISK (Enhanced Due Diligence required):
  - Politically Exposed Persons (PEPs) and their associates
  - Customers from high-risk jurisdictions (FATF grey/black list)
  - Cash-intensive businesses
  - Non-profit organizations
  - Enhanced monitoring: quarterly review + transaction monitoring alerts

SECTION 2: ONGOING MONITORING

2.1 TRANSACTION MONITORING

Financial institutions must implement automated transaction monitoring systems
capable of detecting:
  - Structuring (multiple transactions just below reporting thresholds)
  - Unusual transaction patterns deviating from customer profile
  - Transactions involving high-risk jurisdictions
  - Rapid movement of funds (layering indicators)

Reporting threshold for Currency Transaction Reports (CTR): $10,000
Suspicious Activity Reports (SAR): No threshold — any suspicious activity

2.2 PERIODIC REVIEW

Customer profiles must be reviewed at intervals based on risk rating.
Any change in customer circumstances (address, occupation, ownership) must
trigger a review and potential re-categorization.

SECTION 3: RECORD RETENTION

All KYC documents and transaction records must be retained for a minimum of:
  - 5 years from the date of account closure (customer records)
  - 5 years from the date of transaction (transaction records)
  - 10 years for records related to suspicious activity reports

Electronic records are acceptable provided they are readily retrievable
and protected against unauthorized alteration.
"""

GDPR_FINANCIAL = """
GENERAL DATA PROTECTION REGULATION (GDPR)
APPLICATION TO FINANCIAL SERVICES AND FINTECH COMPANIES

ARTICLE 5: PRINCIPLES RELATING TO PROCESSING OF PERSONAL DATA

Personal data shall be:
(a) processed lawfully, fairly and in a transparent manner (lawfulness, fairness,
    transparency);
(b) collected for specified, explicit and legitimate purposes and not further
    processed in a manner incompatible with those purposes (purpose limitation);
(c) adequate, relevant and limited to what is necessary (data minimisation);
(d) accurate and, where necessary, kept up to date (accuracy);
(e) kept in a form which permits identification for no longer than necessary
    (storage limitation);
(f) processed in a manner that ensures appropriate security (integrity and
    confidentiality).

ARTICLE 6: LAWFUL BASIS FOR PROCESSING

Financial institutions processing customer data must establish one of:
1. Consent: explicit, informed, freely given, withdrawable at any time
2. Contract performance: processing necessary for service delivery
3. Legal obligation: processing required by AML/KYC regulations
4. Legitimate interests: provided not overridden by data subject rights

Note: AML/KYC processing is typically justified under legal obligation (Article 6(1)(c)).
This does NOT eliminate other GDPR obligations — notice requirements, security
measures, and data subject rights still fully apply.

ARTICLE 17: RIGHT TO ERASURE ("RIGHT TO BE FORGOTTEN")

Data subjects may request erasure of their personal data. However, in financial
services, this right is LIMITED where data must be retained for:
  - Legal obligations (AML record keeping: 5 years minimum)
  - Establishment, exercise or defence of legal claims

Financial institutions must document the legal basis for refusing erasure requests.

ARTICLE 25: DATA PROTECTION BY DESIGN AND BY DEFAULT

Financial institutions and fintechs must implement appropriate technical and
organisational measures to ensure data protection principles are integrated
into processing activities from the design phase:

  - Pseudonymisation of customer data where possible
  - Minimum data collection (collect only what is needed for compliance)
  - Access controls limiting staff access to customer data
  - Audit logs of all data access

ARTICLE 32: SECURITY OF PROCESSING

Appropriate technical and organisational measures include:
  - Encryption of personal data at rest and in transit (AES-256 minimum)
  - Ability to restore availability and access after incident
  - Regular testing of security measures
  - Data breach notification to supervisory authority within 72 hours

ARTICLE 83: ADMINISTRATIVE FINES

Infringements of the basic principles (Article 5, 6, 7) are subject to:
  Maximum fine: EUR 20,000,000 or 4% of total worldwide annual turnover
  (whichever is higher)
"""

# ── Internal Bank Policies ────────────────────────────────────────────────────

INTERNAL_AML = """
NEXUS FINANCIAL SERVICES
INTERNAL ANTI-MONEY LAUNDERING POLICY
Document Version: 3.2 | Last Updated: January 2024

1. PURPOSE AND SCOPE

This policy establishes Nexus Financial Services' framework for detecting,
preventing and reporting money laundering activities. It applies to all
employees, contractors, and third-party service providers.

2. CUSTOMER DUE DILIGENCE PROCEDURES

2.1 Standard CDD

CDD is required for all new customers prior to account opening. Our CDD process:
  a) Identity verification using government-issued photo ID
  b) Address verification using utility bill or bank statement
  c) Basic source of funds declaration for accounts expected to exceed $50,000

IMPORTANT POLICY GAP: Our current policy requires CDD only at onboarding.
We do not have a formal ongoing CDD review schedule. Reviews are conducted
on an ad-hoc basis when flagged by transaction monitoring.

2.2 Transaction Thresholds

Currency Transaction Reports (CTR) are filed for cash transactions exceeding $10,000.
Suspicious Activity Reports (SAR) are filed at the discretion of the compliance officer
for transactions that appear unusual.

CURRENT THRESHOLD: Our automated monitoring flags transactions above $9,500 for
manual review (to catch structuring). Below this threshold, automated monitoring
is not applied unless manually requested.

3. RECORD KEEPING

Customer records are retained for 3 years from account closure.
Transaction records are retained for 4 years from transaction date.

4. STAFF TRAINING

AML training is conducted annually for all customer-facing staff.
Compliance team receives quarterly updates.

5. REPORTING STRUCTURE

Suspicious activity is reported to the Chief Compliance Officer (CCO).
The CCO is responsible for filing SARs with FinCEN.
Escalation timeline: Branch staff → Branch Manager → CCO (within 48 hours).
"""

INTERNAL_KYC = """
NEXUS FINANCIAL SERVICES
KNOW YOUR CUSTOMER POLICY
Document Version: 2.1 | Last Updated: March 2024

1. CUSTOMER ONBOARDING REQUIREMENTS

1.1 Individual Customers

Required documentation:
  - Government-issued photo ID (passport or driver's license)
  - Proof of address (utility bill, not older than 6 months)
  - Social Security Number or ITIN

Verification is performed manually by onboarding staff.
Digital/e-KYC is not currently implemented.

1.2 Business Customers

Required documentation:
  - Articles of incorporation
  - EIN verification letter
  - Beneficial ownership form for owners with 25%+ stake

NOTE: We do not currently collect information on the "control person" —
the individual with significant management responsibility. This was
identified as a gap in our last internal audit but has not yet been remediated.

2. RISK RATING

Customers are rated Low, Medium, or High risk at onboarding based on:
  - Country of residence
  - Occupation/industry
  - Expected transaction volume

Review schedule:
  Low risk: Every 3 years
  Medium risk: Every 18 months
  High risk: Annually

3. POLITICALLY EXPOSED PERSONS (PEPs)

PEPs are identified through manual screening against public databases.
Enhanced Due Diligence is applied to all PEPs including:
  - Senior management sign-off on account opening
  - Enhanced transaction monitoring
  - Annual review regardless of assigned risk rating

4. DATA STORAGE

Customer KYC records are stored in our internal CRM system.
Access is restricted to compliance and onboarding teams.
Records are retained per our standard 3-year retention policy.

NOTED GAP: Our 3-year retention policy is shorter than the 5-year minimum
required by FinCEN regulations. This is under review by legal.
"""

INTERNAL_DATA = """
NEXUS FINANCIAL SERVICES
DATA PROTECTION AND PRIVACY POLICY
Document Version: 1.8 | Last Updated: November 2023

1. DATA COLLECTION PRINCIPLES

We collect only the data necessary to provide our services and meet
regulatory obligations. Data is collected with customer consent at
onboarding through our terms of service agreement.

2. DATA STORAGE AND SECURITY

Customer personal data is stored in encrypted databases (AES-128).
Data is backed up daily to our primary data center.
Access to customer data requires role-based authentication.

CURRENT SECURITY MEASURES:
  - Database encryption: AES-128 (at rest)
  - Data in transit: TLS 1.2
  - Access logging: Not currently implemented
  - Penetration testing: Annually

3. DATA RETENTION

Personal data is retained for 3 years following account closure.
This applies to all categories of customer data including identity
documents, transaction records, and communication logs.

4. DATA SUBJECT RIGHTS

Customers may request:
  - Access to their personal data (response within 30 days)
  - Correction of inaccurate data
  - Deletion of their data (subject to regulatory retention requirements)

Data deletion requests are processed within 60 days.

5. DATA BREACH RESPONSE

In the event of a data breach:
  - Internal notification: within 24 hours to CISO
  - Customer notification: within 7 days if data is compromised
  - Regulatory notification: as required by applicable law

6. THIRD PARTY SHARING

Customer data is shared with:
  - Credit bureaus for creditworthiness assessment
  - Regulatory authorities as required by law
  - Service providers under data processing agreements

We do not sell customer data to third parties for marketing purposes.
"""

INTERNAL_CAPITAL = """
NEXUS FINANCIAL SERVICES
CAPITAL ADEQUACY POLICY
Document Version: 2.0 | Last Updated: February 2024

1. CAPITAL REQUIREMENTS

Nexus Financial Services maintains capital ratios in accordance with
applicable regulatory requirements.

TARGET CAPITAL RATIOS:
  Common Equity Tier 1 (CET1): Minimum 6.0% of RWA
  Tier 1 Capital:               Minimum 7.5% of RWA
  Total Capital:                Minimum 9.5% of RWA

NOTE: Our internal targets exceed the Basel III minimums to provide
a buffer above regulatory floors.

2. CAPITAL CONSERVATION BUFFER

We maintain a capital conservation buffer target of 2.0% above minimum
CET1 requirements.

POLICY GAP: Our capital conservation buffer policy does not include the
automatic distribution constraints required under Basel III when the buffer
falls below 2.5%. Our policy allows dividend payments at management
discretion even when the buffer is below regulatory thresholds.

3. LIQUIDITY MANAGEMENT

The treasury team monitors liquidity daily.
LCR is reported to the board monthly.
Target LCR: 110% (above regulatory minimum of 100%).

4. REPORTING

Capital ratios are calculated and reported internally on a monthly basis.
Regulatory reporting is submitted quarterly.

NOTED PROCEDURE: Internal reporting occurs monthly, but our policy does
not specify the 24-hour breach reporting requirement to regulators.
Staff may not be aware that any breach of minimum capital requirements
requires same-day notification to the supervisory authority.
"""


def write_file(directory: str, filename: str, content: str):
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"  Written: {path}")


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    reg_dir = os.path.join(base, "documents", "regulations")
    pol_dir = os.path.join(base, "documents", "internal_policies")

    print("\nGenerating regulatory documents...")
    write_file(reg_dir, "fatf_aml_recommendations.txt",  FATF_AML)
    write_file(reg_dir, "basel_iii_capital_framework.txt", BASEL_CAPITAL)
    write_file(reg_dir, "kyc_compliance_guidelines.txt", KYC_GUIDELINES)
    write_file(reg_dir, "gdpr_financial_services.txt",   GDPR_FINANCIAL)

    print("\nGenerating internal policy documents...")
    write_file(pol_dir, "internal_aml_policy.txt",      INTERNAL_AML)
    write_file(pol_dir, "internal_kyc_policy.txt",       INTERNAL_KYC)
    write_file(pol_dir, "internal_data_policy.txt",      INTERNAL_DATA)
    write_file(pol_dir, "internal_capital_policy.txt",   INTERNAL_CAPITAL)

    print("\nAll sample documents generated successfully.")
    print("Note: In production, replace these with actual PDF files.")
