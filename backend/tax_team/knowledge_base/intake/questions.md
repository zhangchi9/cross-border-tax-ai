# Intake Questions

This file contains all questions used during the intake phase of the tax consultation. Tax experts can edit these questions directly.

## Format Guide
Each question should follow this structure:
- **Question Text**: The actual question asked to the user
- **ID**: Unique identifier (snake_case, no spaces)
- **Action**: What happens when answered "yes" (which module to go to, or which tag to add)
- **Quick Replies**: Suggested response options (optional)

---

## Gating Questions

These are initial screening questions to determine which modules apply to the user's situation.

### Are you a U.S. citizen or U.S. green-card holder?
- **ID**: `us_person_check`
- **Action**: Add tag `us_person_worldwide_filing`; Go to Module A — Residency & Elections
- **Quick Replies**: Yes, No, Not sure

### For this tax year, are you a Canadian tax resident (or unsure about your residency status)?
- **ID**: `canadian_resident_check`
- **Action**: Add tag `canadian_tax_resident_worldwide_filing`; Go to Module A — Residency & Elections
- **Quick Replies**: Yes, No, Not sure

### Did you move between the U.S. and Canada this year, or spend significant time in the other country (e.g., >183 days)?
- **ID**: `cross_border_move`
- **Action**: Add tag `residency_change_dual_status`; Go to Module A — Residency & Elections
- **Quick Replies**: Yes, No

### Do you plan to claim any treaty benefits or elections (e.g., tie-breaker rules, first-year or dual-status elections)?
- **ID**: `treaty_benefits`
- **Action**: Add tag `treaty_based_position`; Go to Module A — Residency & Elections
- **Quick Replies**: Yes, No, Not sure

### Did you earn employment or contractor income in the U.S. at any time this year?
- **ID**: `us_employment`
- **Action**: Add tag `wages_taxable_us_source`; Go to Module B — Employment & U.S. States
- **Quick Replies**: Yes, No

### Did you earn employment or contractor income in Canada at any time this year?
- **ID**: `canada_employment`
- **Action**: Add tag `wages_taxable_canada_source`; Go to Module B — Employment & U.S. States
- **Quick Replies**: Yes, No

### Did you live in one U.S. state and work in another, or work in multiple U.S. states?
- **ID**: `multi_state_work`
- **Action**: Add tag `state_nonconformity_treaty_ftc`; Go to Module B — Employment & U.S. States
- **Quick Replies**: Yes, No

### Do you own or control a business or entity (sole prop, partnership, corporation, LLC/ULC) in the U.S. or Canada?
- **ID**: `business_entity`
- **Action**: Go to Module C — Business & Entities
- **Quick Replies**: Yes, No

### Do you own 10% or more of a foreign corporation/partnership or have a controlled foreign affiliate?
- **ID**: `foreign_corporation`
- **Action**: Add tag `us_shareholder_canadian_corp`; Go to Module C — Business & Entities
- **Quick Replies**: Yes, No, Not sure

### Did you own, buy, sell, or rent out real estate (home, rental, vacation property) in the U.S. or Canada this year?
- **ID**: `real_estate`
- **Action**: Go to Module D — Real Estate
- **Quick Replies**: Yes, No

### Do you want to claim housing-related items (principal residence, moving expenses, home office, or foreign housing exclusions/deductions)?
- **ID**: `housing_related`
- **Action**: Add tag `cross_border_principal_residence`; Go to Module D — Real Estate
- **Quick Replies**: Yes, No

### Do you hold non-registered financial accounts or investments across the border (bank/brokerage accounts, ETFs/mutual funds, bonds, GICs, crypto) located in the U.S. or Canada?
- **ID**: `financial_accounts`
- **Action**: Add tag `cross_border_financial_accounts`; Go to Module E — Investments & Financial Assets
- **Quick Replies**: Yes, No

### Do you have registered accounts or pensions (RRSP, TFSA, RESP, RDSP, 401(k), IRA) or receive government/social benefits (CPP/OAS, EI, U.S. Social Security)?
- **ID**: `registered_accounts`
- **Action**: Add tag `cross_border_retirement_plans`; Go to Module F — Pensions, Savings & Social Benefits
- **Quick Replies**: Yes, No

### Did you receive or exercise equity compensation (RSUs, stock options, ESPP/RSAs) from a U.S. or Canadian employer, including during a cross-border move?
- **ID**: `equity_compensation`
- **Action**: Add tag `equity_compensation_cross_border_workdays`; Go to Module G — Equity Compensation
- **Quick Replies**: Yes, No

### Did you give or receive large gifts or inheritances, or are you a grantor/beneficiary/trustee of a trust (including Canadian trusts with U.S. reporting)?
- **ID**: `gifts_trusts`
- **Action**: Add tag `cross_border_trusts`; Go to Module H — Estates, Gifts & Trusts
- **Quick Replies**: Yes, No, Not sure

### Do you need to file information reports or fix past issues (FBAR/FinCEN 114, IRS Form 8938, CRA T1135, PFIC Form 8621, Forms 3520/3520-A/5471/8865/8858)?
- **ID**: `information_reports`
- **Action**: Add tag `fbar_foreign_account_reporting`; Go to Module I — Reporting & Cleanup
- **Quick Replies**: Yes, No, Not sure

### Do you need to amend prior-year returns or respond to tax notices/assessments from the IRS or CRA?
- **ID**: `amend_returns`
- **Action**: Add tag `compliance_relief_programs`; Go to Module I — Reporting & Cleanup
- **Quick Replies**: Yes, No

### Did you miss any required filings in prior years (e.g., late FBAR/8938/T1135) and want to use a voluntary disclosure/streamlined path?
- **ID**: `missed_filings`
- **Action**: Add tag `compliance_relief_programs`; Go to Module I — Reporting & Cleanup
- **Quick Replies**: Yes, No, Not sure

---

## Module A — Residency & Elections

### U.S. day-count: Did you meet the U.S. Substantial Presence Test (≥ 31 U.S. days this year and 183 weighted total using 1, 1/3, 1/6 rule)?
- **ID**: `a1_substantial_presence`
- **Action**: Add tag `us_resident_substantial_presence`
- **Quick Replies**: Yes, No, Not sure

### Snowbird: Did you spend time in the United States this year but maintain a closer connection to Canada and intend to remain a Canadian tax resident?
- **ID**: `a2_snowbird`
- **Action**: Add tag `snowbird_closer_connection`
- **Quick Replies**: Yes, No

### Residency change: Did you start or cease Canadian or U.S. tax residency at any time this year (immigration/emigration/dual-status)?
- **ID**: `a3_residency_change`
- **Action**: Add tag `residency_change_dual_status`
- **Quick Replies**: Yes, No

### Treaty position: Will you claim a treaty-based position that changes the default result (e.g., Article IV tie-breaker, Article XV short-stay wage exemption, or closer-connection claim)?
- **ID**: `a4_treaty_position`
- **Action**: Add tag `treaty_based_position`
- **Quick Replies**: Yes, No, Not sure

---

## Module B — Employment & U.S. States

### Work Performed While Present

#### Canada → United States: On any day, did you perform work while physically in the United States?
- **ID**: `b1_canada_to_us`
- **Action**: Add tag `wages_taxable_us_source`
- **Quick Replies**: Yes, No

#### U.S. → Canada: On any day, did you perform work while physically in Canada?
- **ID**: `b1_us_to_canada`
- **Action**: Add tag `wages_taxable_canada_source`
- **Quick Replies**: Yes, No

### Treaty Short-Stay Test (answer per direction, if above = Yes)

#### U.S. workdays (Canada → U.S.) meet all three? (≤ 183 U.S. days in relevant 12-month period; employer not U.S. resident; pay not borne by a U.S. PE/fixed base)
- **ID**: `b2_us_workdays`
- **Action**: Add tag `short_stay_treaty_exemption_us`
- **Quick Replies**: Yes - all three, No, Not sure

#### Canadian workdays (U.S. → Canada) meet all three? (≤ 183 Canadian days; employer not Canadian resident; pay not borne by a Canadian PE/fixed base)
- **ID**: `b2_canadian_workdays`
- **Action**: Add tag `short_stay_treaty_exemption_canada`
- **Quick Replies**: Yes - all three, No, Not sure

### Remote Work from Home (no travel)

#### Canada → U.S.: Do you perform services entirely or almost entirely in Canada for a U.S. employer?
- **ID**: `b3_canada_to_us`
- **Action**: Add tag `remote_work_canada_for_us_employer`
- **Quick Replies**: Yes, No

#### U.S. → Canada: Do you perform services entirely or almost entirely in the United States for a Canadian employer?
- **ID**: `b3_us_to_canada`
- **Action**: Add tag `remote_work_us_for_canada_employer`
- **Quick Replies**: Yes, No

### State-Level Issues

#### U.S. state rules: Did a "convenience of the employer" state (e.g., NY/CT/DE/NE) apply to you for remote work?
- **ID**: `b4_state_rules`
- **Action**: Add tag `state_convenience_employer_exposure`
- **Quick Replies**: Yes, No, Not sure

#### U.S. state filing: Will you have a U.S. state income tax return where rules may differ from federal treaty/credit rules?
- **ID**: `b5_state_filing`
- **Action**: Add tag `state_nonconformity_treaty_ftc`
- **Quick Replies**: Yes, No, Not sure

### Social Security & Payroll

#### Social taxes (both directions): Will you use a certificate of coverage under the U.S.–Canada Totalization Agreement to avoid double social security (CPP/EI vs FICA)?
- **ID**: `b6_social_taxes`
- **Action**: Add tag `social_security_totalization`
- **Quick Replies**: Yes, No, Not sure

#### Canada payroll relief (nonresident employer): Do you need Canada Reg. 102/105 waivers or nonresident-employer certification for services performed in Canada?
- **ID**: `b7_canada_payroll`
- **Action**: Add tag `canada_reg_102_105_waivers`
- **Quick Replies**: Yes, No, Not sure

---

## Module C — Business & Entities

### U.S. person → Canadian company: As a U.S. person, did you own (directly/indirectly) ≥ 10% of a Canadian corporation or otherwise control it?
- **ID**: `c1_us_person_canadian_corp`
- **Action**: Add tag `us_shareholder_canadian_corp`
- **Quick Replies**: Yes, No

### Canadian resident → U.S. LLC: As a Canadian resident, did you own any interest in a U.S. LLC (single- or multi-member)?
- **ID**: `c2_canadian_us_llc`
- **Action**: Add tag `canadian_resident_us_llc`
- **Quick Replies**: Yes, No

### Canadian owner of U.S. S-corp: Are you a Canadian owner/investor in a U.S. S-corporation (or planning to be)?
- **ID**: `c3_canadian_us_s_corp`
- **Action**: Add tag `s_corp_shareholder_ineligibility`
- **Quick Replies**: Yes, No

### Canadian indirect tax: Do you likely need to register for Canadian GST/HST for sales/services to Canadian customers?
- **ID**: `c4_canadian_gst_hst`
- **Action**: Add tag `canadian_gst_hst_registration`
- **Quick Replies**: Yes, No, Not sure

### U.S. sales/use tax: Do you have U.S. sales/use tax exposure due to economic nexus or presence in any U.S. state?
- **ID**: `c5_us_sales_tax`
- **Action**: Add tag `us_state_sales_tax_nexus`
- **Quick Replies**: Yes, No, Not sure

---

## Module D — Real Estate

### Canada → United States (rental): Are you a Canadian resident who owns U.S. rental property (including short-term rentals)?
- **ID**: `d1_canadian_us_rental`
- **Action**: Add tag `canadian_resident_us_rental`
- **Quick Replies**: Yes, No

### U.S. (person/resident) → Canada (rental): Are you a U.S. person or Canadian nonresident who owns Canadian rental property (including short-term rentals)?
- **ID**: `d2_us_canadian_rental`
- **Action**: Add tag `us_person_canadian_rental`
- **Quick Replies**: Yes, No

### Selling in the U.S.: Did you (as a non-U.S. resident) sell U.S. real property this year or have a sale pending?
- **ID**: `d3_selling_us`
- **Action**: Add tag `sale_us_real_property_nonresident`
- **Quick Replies**: Yes, No, Pending sale

### Selling in Canada: Did you (as a nonresident of Canada or as a U.S. person) sell Canadian real property this year or have a sale pending?
- **ID**: `d4_selling_canada`
- **Action**: Add tag `sale_canadian_real_property_nonresident`
- **Quick Replies**: Yes, No, Pending sale

### Home sale rules: Was a sold property your home, and are you relying on a principal-residence / U.S. §121 exclusion?
- **ID**: `d5_home_sale`
- **Action**: Add tag `cross_border_principal_residence`
- **Quick Replies**: Yes, No

### Vacancy/speculation: Is your Canadian property subject to local vacancy/speculation/empty-homes taxes?
- **ID**: `d6_vacancy_speculation`
- **Action**: Add tag `local_vacancy_speculation_tax`
- **Quick Replies**: Yes, No, Not sure

### UHT: Do you own Canadian residential property that may be caught by the federal Underused Housing Tax rules?
- **ID**: `d7_uht`
- **Action**: Add tag `underused_housing_tax_uht`
- **Quick Replies**: Yes, No, Not sure

---

## Module E — Investments & Financial Assets

### Canada → United States income: As a Canadian resident, did you receive U.S.-source dividends, interest, or royalties this year?
- **ID**: `e1_canada_us_income`
- **Action**: Add tag `us_investment_income_canadian_resident`
- **Quick Replies**: Yes, No

### U.S. (person/resident) → Canada income: As a U.S. person or Canadian nonresident, did you receive Canadian-source investment income this year?
- **ID**: `e2_us_canada_income`
- **Action**: Add tag `canadian_investment_income_us_person`
- **Quick Replies**: Yes, No

### PFIC (U.S. persons): As a U.S. person, did you hold Canadian mutual funds/ETFs or other non-U.S. pooled funds?
- **ID**: `e3_pfic`
- **Action**: Add tag `pfic_reporting_canadian_funds`
- **Quick Replies**: Yes, No

### Accounts Across the Border

#### Canada → United States: Do you hold U.S. bank/brokerage/retirement/crypto accounts?
- **ID**: `e4_canada_to_us`
- **Action**: Add tag `cross_border_financial_accounts`
- **Quick Replies**: Yes, No

#### U.S. → Canada: Do you hold Canadian bank/brokerage/retirement/crypto accounts?
- **ID**: `e4_us_to_canada`
- **Action**: Add tag `cross_border_financial_accounts`
- **Quick Replies**: Yes, No

### Withholding paperwork: Do you need to furnish/update W-8BEN / W-8ECI / W-9 / CRA NR forms with payers?
- **ID**: `e5_withholding_paperwork`
- **Action**: Add tag `withholding_documentation_maintenance`
- **Quick Replies**: Yes, No, Not sure

---

## Module F — Pensions, Savings & Social Benefits

### Cross-border retirement plans: Do you hold/contribute to RRSP/RRIF, 401(k), or IRA across the border, or did you take distributions this year?
- **ID**: `f1_cross_border_retirement`
- **Action**: Add tag `cross_border_retirement_plans`
- **Quick Replies**: Yes, No

### TFSA/RESP (U.S. persons): Are you a U.S. person with a TFSA or RESP?
- **ID**: `f2_tfsa_resp`
- **Action**: Add tag `tfsa_resp_us_person`
- **Quick Replies**: Yes, No

### Social benefits while abroad: Do you receive U.S. Social Security or Canadian CPP/OAS while living in the other country?
- **ID**: `f3_social_benefits`
- **Action**: Add tag `cross_border_social_benefits`
- **Quick Replies**: Yes, No

### Plan transfers: Do you plan to move/roll retirement funds across the border (directly or indirectly)?
- **ID**: `f4_plan_transfers`
- **Action**: Add tag `cross_border_pension_transfers`
- **Quick Replies**: Yes, No, Considering

---

## Module G — Equity Compensation

### Cross-border workdays: Do your options/RSUs/ESPP have grant/vest/exercise/sale periods that include workdays in both the United States and Canada?
- **ID**: `g1_cross_border_workdays`
- **Action**: Add tag `equity_compensation_cross_border_workdays`
- **Quick Replies**: Yes, No, Not sure

### Detail checks: Do you hold ISOs/NQSOs/ESPP that may require detailed sourcing or AMT checks (for ISOs)?
- **ID**: `g2_detail_checks`
- **Action**: Add tag `detailed_option_espp_iso_allocation`
- **Quick Replies**: Yes, No, Not sure

---

## Module H — Estates, Gifts & Trusts

### Estate exposure (Canada → U.S.): As a Canadian (non-U.S. resident), do you own U.S.-situs assets (U.S. real estate, U.S. company shares, certain U.S. financial assets) that could face U.S. estate tax?
- **ID**: `h1_estate_exposure`
- **Action**: Add tag `us_estate_tax_exposure_nonresident`
- **Quick Replies**: Yes, No, Not sure

### U.S. gifts: Are you making gifts that may require a U.S. gift tax return (you are a U.S. person making large gifts, or gifting U.S.-situs assets)?
- **ID**: `h2_us_gifts`
- **Action**: Add tag `us_gift_tax_return_requirement`
- **Quick Replies**: Yes, No

### Trusts with cross-border ties: Do you create, receive from, or act as trustee/beneficiary of a trust with U.S.–Canada parties or assets?
- **ID**: `h3_trusts`
- **Action**: Add tag `cross_border_trusts`
- **Quick Replies**: Yes, No, Not sure

---

## Module I — Reporting & Cleanup

### FBAR (U.S. persons): If you are a U.S. person, did your non-U.S. accounts (including Canadian) total over USD $10,000 at any time this year?
- **ID**: `i1_fbar`
- **Action**: Add tag `fbar_foreign_account_reporting`
- **Quick Replies**: Yes, No, Not sure

### FATCA (U.S. persons): If you are a U.S. person, do your foreign financial assets (including Canadian) exceed Form 8938 thresholds?
- **ID**: `i2_fatca`
- **Action**: Add tag `fatca_form_8938_reporting`
- **Quick Replies**: Yes, No, Not sure

### T1135 (Canadian residents): If you are a Canadian resident, did the cost of your specified foreign property (including U.S. assets) exceed CAD $100,000 at any time this year?
- **ID**: `i3_t1135`
- **Action**: Add tag `canada_t1135_foreign_property`
- **Quick Replies**: Yes, No, Not sure

### Late filings: Do you have late or missed filings (returns, FBAR/8938/T1135, info forms) needing an amnesty/disclosure path?
- **ID**: `i4_late_filings`
- **Action**: Add tag `compliance_relief_programs`
- **Quick Replies**: Yes, No

---

## Notes for Tax Team

- All IDs must be unique across all questions
- Use snake_case for IDs (lowercase with underscores)
- Quick replies are optional but recommended
- Actions should clearly state either "Go to Module X" or "Add tag `tag_name`"
- Keep questions conversational and avoid jargon
- Never ask for sensitive information (SSN, SIN, account numbers)