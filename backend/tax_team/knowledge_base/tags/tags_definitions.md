# Tag Definitions

This file defines all tax tags used by the AI system. Each tag represents a specific tax situation and includes the forms required for compliance.

## Format Guide

Each tag should follow this structure:

```markdown
## tag_id

**Name**: Human-readable tag name

**Description**: Clear explanation of the tax situation in plain English

**Forms:**

### United States
- **Form Name**: Description or purpose
- **Form Name**: Description or purpose

### Canada
- **Form Name**: Description or purpose

**Why**: Brief justification for why these forms are required
```

---

## Residency & Treaty Status Tags

### us_person_worldwide_filing

**Name**: U.S. person (citizen/green-card holder) - worldwide U.S. filing

**Description**: You are a U.S. citizen or U.S. lawful permanent resident (green-card holder). The U.S. taxes you on worldwide income each year, regardless of where you live. You generally use the foreign tax credit to relieve double taxation; foreign asset/account reporting may also apply.

**Forms:**

### United States
- **Form 1040**: Annual U.S. individual income tax return reporting worldwide income
- **Form 1116**: Claim credit for income tax paid to Canada to mitigate double tax
- **Form 8938**: Report specified foreign financial assets if thresholds are met (FATCA)
- **FinCEN Form 114 (FBAR)**: Report non-U.S. financial accounts if aggregate balance exceeds USD $10,000 at any time

**Why**: U.S. persons must report worldwide income on Form 1040; Form 1116 prevents double taxation. Form 8938 and FBAR satisfy foreign asset/account disclosure when thresholds are met.

---

### canadian_tax_resident_worldwide_filing

**Name**: Canadian tax resident (worldwide Canadian filing)

**Description**: You are a resident of Canada for tax purposes (factual or deemed). Canada taxes residents on worldwide income; foreign tax credits may be claimed for U.S. taxes paid. Foreign asset reporting may also apply.

**Forms:**

### Canada
- **T1 General**: Annual Canadian individual income tax return reporting worldwide income
- **Schedule T2209**: Claim federal foreign tax credit for U.S. income taxes paid
- **Form T1135**: Report specified foreign property if cost amount exceeded CAD $100,000 at any time (Foreign income verification statement)

**Why**: Canadian residents report worldwide income on the T1; Schedule T2209 provides federal foreign tax credit relief for U.S.-taxed income. T1135 fulfills foreign asset disclosure when thresholds are met.

---

### us_resident_substantial_presence

**Name**: U.S. resident by substantial presence test

**Description**: You spent enough days physically in the U.S. this year (weighted 3-year formula) to be treated as a U.S. tax resident. You file a full U.S. resident return unless you qualify for an exception (e.g., closer connection).

**Forms:**

### United States
- **Form 1040**: Annual U.S. individual income tax return (or Form 1040-NR if claiming an exception)
- **Form 8840**: Closer Connection Exception to Substantial Presence Test (if claiming nonresident exception)

**Why**: Establishes your U.S. tax status; Form 8840 is required to claim the closer-connection exception to SPT.

---

### snowbird_closer_connection

**Name**: Snowbird with closer connection to Canada (Form 8840)

**Description**: You were in the U.S. enough days to otherwise meet the Substantial Presence Test but keep stronger ties to Canada and qualify to be taxed as a U.S. nonresident.

**Forms:**

### United States
- **Form 8840**: Stand-alone if no 1040-NR is required, or attached to 1040-NR if you must file

**Why**: Discloses the treaty/closer-connection facts so the IRS accepts nonresident status.

---

### residency_change_dual_status

**Name**: Residency change / dual-status year

**Description**: You became or ceased to be a U.S. resident mid-year (or vice-versa for Canada). This triggers departure tax rules in Canada and dual-status filing in the U.S.

**Forms:**

### United States
- **Form 1040**: Dual-status statement attached
- **Form 8833**: Treaty-based return position disclosure
- **Form 1040-NR**: For nonresident portion of year

### Canada
- **T1 General**: With emigration/immigration disclosure
- **Form T1161**: List of properties by an emigrant
- **Schedule 3**: Capital gains/losses (for departure tax)

**Why**: Both countries tax differently based on residency status; departure from Canada may trigger deemed disposition tax.

---

### treaty_based_position

**Name**: Treaty-based position disclosure (Form 8833 likely required)

**Description**: You are claiming a treaty-based position that overrides or modifies U.S. tax law (e.g., Article IV tie-breaker, Article XV short-stay wage exemption, or closer-connection claim).

**Forms:**

### United States
- **Form 8833**: Treaty-Based Return Position Disclosure (required for most treaty positions)

**Why**: The IRS requires disclosure when you take a position based on a tax treaty that reduces U.S. tax.

---

## Employment & Wages Tags

### wages_taxable_us_source

**Name**: Wages taxable in the United States based on U.S. workdays (source-country wages)

**Description**: You performed work while physically present in the United States. Those wages are generally U.S.-source income subject to U.S. taxation.

**Forms:**

### United States
- **Form 1040 or 1040-NR**: Report U.S.-source wages
- **Form 1116**: Foreign tax credit if also taxed by Canada (for U.S. persons/residents)

### Canada
- **T1 General**: Report employment income
- **Schedule T2209**: Foreign tax credit for U.S. taxes paid

**Why**: Source-country taxation applies to wages earned while physically present in that country.

---

### wages_taxable_canada_source

**Name**: Wages taxable in Canada based on Canadian workdays (source-country wages)

**Description**: You performed work while physically present in Canada. Those wages are generally Canadian-source income subject to Canadian taxation.

**Forms:**

### Canada
- **T1 General**: Report Canadian employment income
- **Schedule T2209**: Foreign tax credit if also taxed by U.S.

### United States
- **Form 1040**: Report worldwide income (if U.S. person)
- **Form 1116**: Foreign tax credit for Canadian taxes paid

**Why**: Source-country taxation applies to wages earned while physically present in that country.

---

### short_stay_treaty_exemption_us

**Name**: Short-stay treaty exemption for wages (United States)

**Description**: You qualify for the treaty short-stay exemption under Article XV (≤183 days, non-U.S. employer, not borne by U.S. PE). U.S. wages may be exempt from U.S. taxation.

**Forms:**

### United States
- **Form 8833**: Treaty-based return position disclosure
- **Form W-4**: Claim exemption from withholding with employer

**Why**: Treaty exemption must be disclosed to IRS; withholding exemption claimed with employer.

---

### short_stay_treaty_exemption_canada

**Name**: Short-stay treaty exemption for wages (Canada)

**Description**: You qualify for the treaty short-stay exemption under Article XV (≤183 days, non-Canadian employer, not borne by Canadian PE). Canadian wages may be exempt from Canadian taxation.

**Forms:**

### Canada
- **Form R105**: Request for waiver of Canadian tax withholding

**Why**: Treaty exemption allows you to request waiver of Canadian withholding on wages.

---

### remote_work_canada_for_us_employer

**Name**: Remote work performed in Canada for U.S. employer (sourcing & FTC coordination)

**Description**: You work remotely from Canada for a U.S. employer. Canada sources and taxes this income; U.S. may also tax depending on your status.

**Forms:**

### Canada
- **T1 General**: Report employment income
- **Schedule T2209**: Foreign tax credit (if applicable)

### United States
- **Form 1040**: Report income (if U.S. person)
- **Form 1116**: Foreign tax credit for Canadian taxes paid

**Why**: Remote work is typically sourced where services are performed (Canada), requiring FTC coordination.

---

### remote_work_us_for_canada_employer

**Name**: Remote work performed in the United States for Canadian employer (sourcing & FTC coordination)

**Description**: You work remotely from the U.S. for a Canadian employer. U.S. sources and taxes this income; Canada may also tax depending on your status.

**Forms:**

### United States
- **Form 1040 or 1040-NR**: Report employment income
- **Form 1116**: Foreign tax credit (if applicable)

### Canada
- **T1 General**: Report income (if Canadian resident)
- **Schedule T2209**: Foreign tax credit for U.S. taxes paid

**Why**: Remote work is typically sourced where services are performed (U.S.), requiring FTC coordination.

---

### state_convenience_employer_exposure

**Name**: State convenience-of-employer exposure

**Description**: Certain U.S. states (NY, CT, DE, NE, PA, AR) tax wages based on where your employer is located, not where you work. This can create exposure even if you're working remotely from another state or Canada.

**Forms:**

### United States (State)
- **State Income Tax Return**: For the convenience-of-employer state (e.g., NY IT-201)

**Why**: These states have non-conforming rules that may override federal treaty protections.

---

### state_nonconformity_treaty_ftc

**Name**: State nonconformity with treaty/FTC

**Description**: Your U.S. state income tax return may not follow federal treaty rules or foreign tax credit calculations, creating additional state tax liability.

**Forms:**

### United States (State)
- **State Income Tax Return**: Check state-specific FTC and treaty conformity rules

**Why**: States are not bound by federal tax treaties and have their own FTC rules.

---

### social_security_totalization

**Name**: Social security Totalization & certificate of coverage

**Description**: The U.S.-Canada Totalization Agreement prevents double social security taxation. You need a certificate of coverage to prove which country's system covers you.

**Forms:**

### United States
- **Form SSA-1945**: Application for certificate of coverage (U.S. coverage)

### Canada
- **CPP/QPP Certificate of Coverage**: Request from Service Canada

**Why**: Certificate prevents double payment of CPP/EI and FICA taxes.

---

### canada_reg_102_105_waivers

**Name**: Canada Reg. 102/105 waivers & nonresident-employer certification

**Description**: When a nonresident employer has employees working in Canada, Canadian tax withholding may be waived if certain conditions are met.

**Forms:**

### Canada
- **Form R102**: Regulation 102 waiver application
- **Form R105**: Regulation 105 waiver application

**Why**: Reduces administrative burden for nonresident employers with limited Canadian presence.

---

## Real Estate Tags

### canadian_resident_us_rental

**Name**: Canadian resident owning U.S. rental property

**Description**: As a Canadian resident, you own rental property in the United States. This creates U.S. tax filing obligations and potential withholding requirements on rental income.

**Forms:**

### United States
- **Form 1040-NR**: U.S. nonresident income tax return reporting rental income
- **Form W-8ECI**: Certificate of foreign person's claim that income is effectively connected with U.S. trade or business (to avoid 30% withholding)
- **State Tax Return**: State income tax return where property is located

### Canada
- **T1 General**: Report worldwide income including U.S. rental income
- **Schedule T2209**: Claim foreign tax credit for U.S. taxes paid on rental income
- **Form T776**: Statement of real estate rentals

**Why**: U.S. taxes nonresidents on U.S.-source rental income; Canada taxes residents on worldwide income. Proper reporting and foreign tax credits prevent double taxation.

---

### us_person_canadian_rental

**Name**: U.S. person owning Canadian rental property

**Description**: As a U.S. person, you own rental property in Canada. This creates Canadian tax filing obligations and potential withholding requirements on rental income.

**Forms:**

### Canada
- **T1 General**: Canadian income tax return reporting rental income (if required to file)
- **NR4**: Statement of amounts paid or credited to nonresidents (for withholding purposes)
- **Form T776**: Statement of real estate rentals

### United States
- **Form 1040**: Report worldwide income including Canadian rental income
- **Form 1116**: Claim foreign tax credit for Canadian taxes paid on rental income
- **Schedule E**: Supplemental income and loss (rental income)

**Why**: Canada taxes nonresidents on Canadian-source rental income; U.S. taxes citizens on worldwide income. Proper reporting and foreign tax credits prevent double taxation.

---

### cross_border_principal_residence

**Name**: Cross-border principal residence exemption

**Description**: You're claiming principal residence exemption on a home sale in either U.S. (§121 exclusion) or Canada (principal residence exemption), and need to coordinate with the other country's rules.

**Forms:**

### United States
- **Form 1040**: Report home sale and claim §121 exclusion if applicable
- **Form 8949**: Sales and other dispositions of capital assets
- **Schedule D**: Capital gains and losses

### Canada
- **T1 General**: Report home sale and claim principal residence exemption
- **Schedule 3**: Capital gains or losses
- **Form T2091**: Designation of a property as a principal residence

**Why**: Both countries have principal residence exemptions, but rules differ. Proper designation and reporting ensures optimal tax treatment in both jurisdictions.

---

### sale_us_real_property_nonresident

**Name**: Sale of U.S. real property by nonresident (FIRPTA)

**Description**: You sold U.S. real property as a nonresident. FIRPTA requires 15% withholding on gross sales price unless you obtain a withholding certificate.

**Forms:**

### United States
- **Form 1040-NR**: Report capital gain from U.S. real property sale
- **Form 8288**: U.S. withholding tax return for dispositions by foreign persons of U.S. real property interests
- **Form 8288-B**: Application for withholding certificate for dispositions by foreign persons of U.S. real property interests
- **State Tax Return**: State capital gains tax return

**Why**: FIRPTA (Foreign Investment in Real Property Tax Act) requires withholding and filing to ensure nonresidents pay U.S. tax on gains from U.S. real estate sales.

---

### sale_canadian_real_property_nonresident

**Name**: Sale of Canadian real property by nonresident (Section 116)

**Description**: You sold Canadian real property as a nonresident. Section 116 requires clearance certificate and withholding unless you obtain proper clearance.

**Forms:**

### Canada
- **Form T2062**: Request by a non-resident of Canada for a certificate of compliance related to the disposition of taxable Canadian property
- **Form T2062A**: Request by a non-resident of Canada for a certificate of compliance related to the disposition of Canadian resource or timber resource property
- **T1 General**: Nonresident income tax return to report capital gain

**Why**: Section 116 clearance ensures nonresidents pay Canadian tax on gains from Canadian property sales. Buyer withholds 25% of purchase price if no clearance certificate obtained.

---

### local_vacancy_speculation_tax

**Name**: Local vacancy or speculation tax (BC, Vancouver, etc.)

**Description**: Your Canadian property may be subject to local vacancy taxes, speculation taxes, or empty homes taxes imposed by provincial or municipal governments.

**Forms:**

### Canada (Provincial/Municipal)
- **BC Speculation and Vacancy Tax Declaration**: Annual declaration for B.C. properties
- **Vancouver Empty Homes Tax Declaration**: Annual declaration for Vancouver properties
- **Other municipal declarations**: Varies by jurisdiction

**Why**: Provincial and municipal governments impose these taxes to address housing affordability. Annual declarations required even if exemption applies.

---

### underused_housing_tax_uht

**Name**: Underused Housing Tax (UHT)

**Description**: You own Canadian residential property that may be subject to the federal Underused Housing Tax (UHT) of 1% of property value annually.

**Forms:**

### Canada
- **Form UHT-2900**: Underused Housing Tax Return and Election Form

**Why**: Federal UHT applies to Canadian residential property owned by non-Canadians and certain other owners. Annual filing required even if exemption applies; penalty for late filing is $5,000 minimum.

---

## Investment & Financial Asset Tags

### us_investment_income_canadian_resident

**Name**: U.S. investment income received by Canadian resident

**Description**: As a Canadian resident, you receive U.S.-source dividends, interest, or royalties. These are subject to U.S. withholding and Canadian taxation with foreign tax credit relief.

**Forms:**

### United States
- **Form W-8BEN**: Certificate of foreign status (provide to U.S. payers to claim treaty-reduced withholding rates)
- **Form 1040-NR**: Only if required (certain circumstances)

### Canada
- **T1 General**: Report all investment income
- **Schedule T2209**: Claim foreign tax credit for U.S. withholding taxes
- **T5/T3**: Information slips from Canadian financial institutions

**Why**: U.S. withholds tax on U.S.-source investment income paid to nonresidents; Canada taxes residents on worldwide income. Treaty rates and foreign tax credits prevent double taxation.

---

### canadian_investment_income_us_person

**Name**: Canadian investment income received by U.S. person

**Description**: As a U.S. person, you receive Canadian-source dividends, interest, or royalties. These are subject to Canadian withholding and U.S. taxation with foreign tax credit relief.

**Forms:**

### Canada
- **Form NR301**: Declaration of eligibility for benefits under a tax treaty (provide to Canadian payers for reduced withholding)

### United States
- **Form 1040**: Report all investment income
- **Form 1116**: Claim foreign tax credit for Canadian withholding taxes
- **Schedule B**: Interest and ordinary dividends

**Why**: Canada withholds tax on Canadian-source investment income paid to nonresidents; U.S. taxes citizens on worldwide income. Treaty rates and foreign tax credits prevent double taxation.

---

### cross_border_financial_accounts

**Name**: Cross-border financial accounts (FBAR, FATCA, T1135 reporting)

**Description**: You hold financial accounts (bank, brokerage, retirement, crypto) in the other country, triggering disclosure requirements FBAR, Form 8938, and/or T1135.

**Forms:**

### United States (if U.S. person)
- **FinCEN Form 114 (FBAR)**: If non-U.S. accounts exceed $10,000 at any time
- **Form 8938**: If foreign financial assets exceed thresholds

### Canada (if Canadian resident)
- **Form T1135**: If foreign property cost exceeds CAD $100,000 at any time

**Why**: Both countries require disclosure of foreign financial accounts to ensure worldwide income reporting and combat tax evasion.

---

### pfic_reporting_canadian_funds

**Name**: PFIC reporting for Canadian mutual funds and ETFs (Form 8621)

**Description**: As a U.S. person, you hold Canadian mutual funds, ETFs, or other non-U.S. pooled investment funds that are classified as Passive Foreign Investment Companies (PFICs), requiring complex annual reporting.

**Forms:**

### United States
- **Form 8621**: Information return by a shareholder of a passive foreign investment company (required for EACH PFIC)
- **Form 1040**: Report PFIC income or gains

**Why**: U.S. tax law treats PFICs punitively to discourage offshore investing. Complex reporting and unfavorable tax treatment (interest charge, no capital gains rates) unless QEF or mark-to-market election made.

---

### withholding_documentation_maintenance

**Name**: Withholding documentation maintenance (W-8BEN, W-9, NR forms)

**Description**: You need to furnish or update withholding certificates with payers in both countries to claim treaty benefits or avoid incorrect withholding.

**Forms:**

### United States
- **Form W-8BEN**: For nonresidents receiving U.S.-source income (claim treaty benefits)
- **Form W-9**: For U.S. persons receiving payments (provide TIN to payers)

### Canada
- **Form NR301**: Declaration of eligibility for treaty benefits
- **Form R105**: Regulation 105 waiver application

**Why**: Proper withholding documentation ensures correct withholding rates and avoids over-withholding or penalties. Forms typically expire after 3 years.

---

## Pension & Retirement Tags

### cross_border_retirement_plans

**Name**: Cross-border retirement plans (RRSP, RRIF, 401(k), IRA)

**Description**: You hold or contribute to retirement accounts in both countries, requiring coordination of reporting, withholding, and tax treatment under treaty provisions.

**Forms:**

### United States (if U.S. person with RRSP/RRIF)
- **Form 8891**: U.S. information return for beneficiaries of certain Canadian registered retirement plans (discontinued, now Form 8938)
- **Form 8938**: Report RRSP/RRIF if thresholds met
- **Form 1040**: Report distributions if not properly deferred under treaty

### Canada (if Canadian resident with 401(k)/IRA)
- **T1 General**: Report distributions
- **Schedule T2209**: Foreign tax credit for U.S. withholding
- **Treaty election**: Election to defer taxation under Article XVIII

**Why**: Treaty provisions allow deferral of taxation on retirement accounts, but proper elections and reporting required. Distributions subject to withholding and coordination.

---

### cross_border_social_benefits

**Name**: Cross-border social benefits (CPP/OAS, U.S. Social Security)

**Description**: You receive social security or pension benefits from one country while residing in or being a tax resident of the other country.

**Forms:**

### United States
- **Form 1040 or 1040-NR**: Report CPP/OAS as foreign pension income
- **Form 8833**: Treaty position if claiming exemption for OAS

### Canada
- **T1 General**: Report U.S. Social Security benefits (85% taxable in Canada under treaty)
- **Schedule T2209**: Foreign tax credit if U.S. withheld taxes

**Why**: Treaty determines which country can tax social benefits and at what rate. CPP/OAS generally taxable in both countries; U.S. Social Security 85% taxable in Canada; proper reporting and credits prevent double taxation.

---

### tfsa_resp_us_person

**Name**: TFSA or RESP held by U.S. person

**Description**: As a U.S. person, you hold a Tax-Free Savings Account (TFSA) or Registered Education Savings Plan (RESP). These are NOT recognized as tax-advantaged by the U.S., creating annual reporting and taxation requirements.

**Forms:**

### United States
- **Form 3520**: Annual return to report transactions with foreign trust (TFSA/RESP treated as foreign grantor trust)
- **Form 3520-A**: Annual information return of foreign trust with U.S. owner
- **Form 1040**: Report all income from TFSA/RESP annually (no tax-free treatment)

### Canada
- **T1 General**: TFSA/RESP contributions and withdrawals (tax-free in Canada)

**Why**: U.S. does not recognize TFSA/RESP as qualified retirement plans under the treaty. All income is taxable annually to U.S. person, and complex trust reporting required. Severe penalties for non-filing.

---

### cross_border_pension_transfers

**Name**: Cross-border pension transfers or rollovers

**Description**: You plan to transfer or roll over retirement funds between U.S. and Canadian retirement accounts (e.g., 401(k) to RRSP, or vice versa).

**Forms:**

### United States
- **Form 1040**: Report distribution and rollover
- **Form 5498**: IRA contribution information
- **Form 8891**: RRSP election (if applicable)

### Canada
- **T1 General**: Report transfer
- **T4RSP/T4RIF**: Information slip for RRSP/RRIF
- **RC267**: Employee contributions to a Canadian or U.S. retirement plan

**Why**: Direct transfers between U.S. and Canadian retirement accounts generally not permitted without tax consequences. Proper planning required to minimize withholding and taxes.

---

## Equity Compensation Tags

### equity_compensation_cross_border_workdays

**Name**: Equity compensation with cross-border workdays

**Description**: Your stock options, RSUs, or ESPP have grant, vest, exercise, or sale periods that span time working in both U.S. and Canada, requiring complex sourcing allocation.

**Forms:**

### United States
- **Form 1040 or 1040-NR**: Report equity compensation income
- **Form 3921**: Exercise of incentive stock option (ISO)
- **Form 3922**: Transfer of stock acquired through ESPP
- **Form 6251**: Alternative minimum tax (if ISOs)

### Canada
- **T1 General**: Report equity compensation income
- **Form T1135**: If holding foreign shares exceeds threshold
- **Schedule 3**: Capital gains on sale

**Why**: Equity compensation is sourced based on workdays in each country during vesting/earning period. Complex allocation formulas required to determine each country's taxing rights and prevent double taxation.

---

### detailed_option_espp_iso_allocation

**Name**: Detailed option/ESPP/ISO allocation and AMT analysis

**Description**: You hold incentive stock options (ISOs), non-qualified stock options (NQSOs), or participate in ESPP requiring detailed cross-border sourcing and potential AMT analysis.

**Forms:**

### United States
- **Form 6251**: Alternative minimum tax (ISOs trigger AMT)
- **Form 3921**: ISO exercise
- **Form 3922**: ESPP transfer
- **Form 1040**: Report compensation and capital gains

### Canada
- **T1 General**: Report employment benefit and capital gains
- **Form T1135**: Report foreign shares if threshold met
- **Schedule 3**: Capital gains on sale

**Why**: ISOs trigger AMT in U.S.; cross-border moves complicate sourcing; ESPP has special holding period rules. Detailed day-by-day allocation may be required for accuracy and tax treaty application.

---

## Estates, Gifts & Trust Tags

### us_estate_tax_exposure_nonresident

**Name**: U.S. estate tax exposure for nonresident

**Description**: As a nonresident of the U.S., you own U.S.-situs assets (U.S. real estate, U.S. company stock, certain U.S. financial assets) that could face U.S. estate tax upon death, with only $60,000 exemption.

**Forms:**

### United States (upon death)
- **Form 706-NA**: U.S. estate tax return for nonresident aliens
- **Treaty election**: Claim treaty benefits for higher exemption under Article XXIX B

**Why**: U.S. imposes estate tax on U.S.-situs assets owned by nonresidents. Exemption only $60,000 (vs. $13.61M for U.S. persons). Treaty provides pro-rata unified credit based on worldwide estate.

---

### us_gift_tax_return_requirement

**Name**: U.S. gift tax return requirement

**Description**: You made or received gifts that may require U.S. gift tax reporting. U.S. persons making large gifts, or gifting U.S.-situs assets, may need to file Form 709.

**Forms:**

### United States
- **Form 709**: U.S. gift (and generation-skipping transfer) tax return

**Why**: U.S. taxes large gifts made by U.S. persons. Gifts of U.S.-situs property by nonresidents also taxable. Annual exclusion ($18,000 in 2024) and lifetime exemption ($13.61M) apply to U.S. persons.

---

### cross_border_trusts

**Name**: Cross-border trusts (Forms 3520/3520-A)

**Description**: You create, receive distributions from, or act as trustee/beneficiary of a trust with U.S. and Canadian parties or assets, triggering complex reporting in both countries.

**Forms:**

### United States (if U.S. person involved)
- **Form 3520**: Annual return to report transactions with foreign trusts and receipt of certain foreign gifts
- **Form 3520-A**: Annual information return of foreign trust with U.S. owner
- **Form 8938**: Report foreign trust if thresholds met

### Canada
- **T3**: Trust income tax return
- **T1135**: If foreign property exceeds threshold
- **T1141**: Information return in respect of contributions to non-resident trusts

**Why**: Cross-border trusts face complex tax treatment in both countries. U.S. has severe penalties for non-reporting (35% of value for Form 3520-A). Proper planning and reporting essential.

---

## Business & Entity Tags

### us_shareholder_canadian_corp

**Name**: U.S. shareholder of Canadian corporation (Forms 5471; GILTI/Subpart F)

**Description**: As a U.S. person owning ≥10% of a Canadian corporation, you have extensive U.S. reporting requirements including potential GILTI (Global Intangible Low-Taxed Income) and Subpart F income inclusion.

**Forms:**

### United States
- **Form 5471**: Information return of U.S. persons with respect to certain foreign corporations
- **Form 8992**: U.S. shareholder calculation of GILTI
- **Form 8993**: Section 250 deduction for GILTI
- **Form 1040 Schedule 3**: Report additional income

**Why**: U.S. tax law requires extensive reporting and may tax corporate earnings before distribution.

---

### canadian_resident_us_llc

**Name**: Canadian resident owning U.S. LLC (entity classification mismatch planning)

**Description**: As a Canadian resident owning a U.S. LLC, there's a classification mismatch: U.S. treats it as transparent (pass-through), Canada may treat it as a corporation. This requires careful tax planning.

**Forms:**

### United States
- **Form 1040-NR**: Report U.S.-source income (if LLC has U.S. operations)
- **Form 1065**: U.S. partnership return (if multi-member LLC)

### Canada
- **T1 General**: Report income
- **T1134**: Information return relating to controlled and not-controlled foreign affiliates
- **T2**: Corporate tax return (if LLC elected corporate treatment in Canada)

**Why**: Classification mismatch can cause timing differences and potential double taxation without proper planning.

---

### s_corp_shareholder_ineligibility

**Name**: S-corporation shareholder ineligibility for Canadian owners (planning required)

**Description**: Canadian residents generally cannot be shareholders of U.S. S-corporations. If you become a Canadian resident while owning S-corp shares, the election may terminate.

**Forms:**

### United States
- **Form 1120S**: S-corporation return (may need to convert to C-corp)
- **Form 2553**: Election to be treated as S-corporation (potential termination)

**Why**: S-corp eligibility rules require all shareholders to be U.S. persons; Canadian residency terminates the election.

---

### canadian_gst_hst_registration

**Name**: Canadian GST/HST registration (place-of-supply rules)

**Description**: If you make taxable supplies to Canadian customers exceeding CAD $30,000, you must register for and collect GST/HST.

**Forms:**

### Canada
- **Form RC1**: GST/HST registration
- **GST/HST Return**: Filed monthly, quarterly, or annually depending on revenue

**Why**: Canadian law requires businesses making taxable supplies to Canadian customers to register for GST/HST.

---

### us_state_sales_tax_nexus

**Name**: U.S. state sales/use tax nexus

**Description**: Economic nexus rules in many U.S. states require businesses to collect and remit sales tax based on sales volume or transaction count, even without physical presence.

**Forms:**

### United States (State)
- **State Sales Tax Registration**: Varies by state
- **State Sales Tax Return**: Varies by state (typically monthly or quarterly)

**Why**: Post-Wayfair ruling established economic nexus for sales tax obligations.

---

## Reporting & Compliance Tags

### fbar_foreign_account_reporting

**Name**: FBAR foreign account reporting (FinCEN 114)

**Description**: As a U.S. person with non-U.S. financial accounts totaling over USD $10,000 at any time during the year, you must file FBAR.

**Forms:**

### United States
- **FinCEN Form 114**: Foreign Bank Account Report (filed electronically, separate from tax return)

**Why**: U.S. law requires disclosure of foreign financial accounts to combat money laundering and tax evasion.

---

### fatca_form_8938_reporting

**Name**: FATCA Form 8938 reporting

**Description**: As a U.S. person, if your foreign financial assets exceed certain thresholds (varies by filing status and residence), you must file Form 8938 with your tax return.

**Forms:**

### United States
- **Form 8938**: Statement of Specified Foreign Financial Assets (filed with Form 1040)

**Why**: FATCA (Foreign Account Tax Compliance Act) requires reporting of specified foreign financial assets above threshold amounts.

---

### canada_t1135_foreign_property

**Name**: Canada T1135 foreign property reporting

**Description**: As a Canadian resident, if the cost of your specified foreign property exceeded CAD $100,000 at any time during the year, you must file Form T1135.

**Forms:**

### Canada
- **Form T1135**: Foreign Income Verification Statement

**Why**: Canadian law requires disclosure of foreign property to ensure worldwide income reporting.

---

### compliance_relief_programs

**Name**: Compliance relief programs (IRS Streamlined / CRA Voluntary Disclosures)

**Description**: If you have late or missed filings, you may qualify for amnesty programs with reduced penalties.

**Forms:**

### United States
- **Streamlined Filing Compliance Procedures**: For U.S. taxpayers residing outside the U.S.
- **Streamlined Domestic Offshore Procedures**: For U.S. taxpayers residing in the U.S.
- **Delinquent FBAR Submission Procedures**: For FBAR-only issues
- **Delinquent International Information Return Submission Procedures**: For late Forms 5471, 8938, etc.

### Canada
- **Voluntary Disclosures Program (VDP)**: CRA program for voluntary disclosure of unreported income or unfiled returns

**Why**: These programs allow taxpayers to come into compliance with reduced or eliminated penalties if non-compliance was non-willful.

---

## Notes for Tax Team

- Each tag ID must be unique and use snake_case
- Descriptions should be clear and avoid excessive jargon
- Forms should be listed with brief explanations
- "Why" section should justify the forms requirement
- Always specify jurisdiction (United States, Canada, or State)
- Keep descriptions focused on practical implications
- Update forms if tax law changes

## Adding New Tags

To add a new tag:
1. Choose a unique snake_case ID
2. Write a clear name and description
3. List all required forms by jurisdiction
4. Explain why these forms are required
5. Link tag to appropriate intake question in `questions.md`
6. Commit changes with descriptive message