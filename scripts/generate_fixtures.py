#!/usr/bin/env python3
"""Generate synthetic IRS Tax Return Transcript PDFs for testing.

All data is fictional. Names, SSNs, addresses, and financial figures
are entirely made up and do not correspond to any real person.
"""

import fitz  # PyMuPDF


def _write_transcript_pdf(output_path: str, pages: list[str], total_pages: int) -> None:
    """Write a multi-page PDF from text content."""
    doc = fitz.open()
    for i, page_text in enumerate(pages):
        # Use a tall page to fit all the IRS transcript content
        page = doc.new_page(width=612, height=1800)
        page.insert_text(
            fitz.Point(36, 36),
            page_text,
            fontsize=9,
            fontname="helv",
        )
    doc.save(output_path)
    doc.close()
    print(f"  Generated: {output_path}")


def generate_2021_with_distributions() -> None:
    """Generate a 2021 transcript with IRA distributions and Form 8606.

    Scenario: Person contributed $6,000/year nondeductible to Traditional IRA
    for 2019-2021, then converted $99,000 in 2021. Has $18,000 basis,
    IRA FMV was ~$105,000 before conversion.
    """
    page1 = """Page 1/6
This Product Contains Sensitive Taxpayer Data
Form 1040 Tax Return Transcript
 
Request Date:
03-15-2026
 
Response Date:
03-15-2026
 
Tracking Number:
100000000001
 
SSN provided:
XXX-XX-1234
 
Report for Tax Period Ending:
12-31-2021
The following items reflect the amount as shown on the return, and the amount as adjusted, if applicable. They do not show subsequent 
activity on the account.
 
SSN:
XXX-XX-1234
 
Spouse SSN:
 
JANE A DOE
 
100 MAIN ST
 
Filing status:
Single Taxpayer
 
Form number:
1040
 
Cycle posted:
20221305
 
Received date:
04-15-2022
 
Payment:
$0.00
 
Exemption number:
01
 
PTIN:
XXX-XX-9999
 
Preparer EIN:
XX-XXX0001
Income
 
Wages, salaries, tips, etc:
$150,000.00
 
Taxable interest income (Schedule B):
$250.00
 
Tax-exempt interest:
$0.00
 
Ordinary dividend income (Schedule B):
$1,200.00
 
Qualified dividends:
$800.00
 
Refunds of state/local taxes:
$0.00
 
Alimony received:
$0.00
 
Business income or loss (Schedule C):
$0.00
 
Business income or loss (Schedule C) per computer:
$0.00
 
Capital gain or loss (Schedule D):
$500.00
 
Capital gains or loss (Schedule D) per computer:
$500.00
 
Other gains or losses (Form 4797):
$0.00
 
Total IRA distributions:
$99,000.00
 
Taxable IRA distributions:
$82,029.00
 
Total pensions and annuities:
$0.00
 
Taxable pension/annuity amount:
$0.00
 
Additional income:
$0.00
 
Additional income per computer:
$0.00
 
Refundable credits per computer:
$0.00
 
Qualified business income deduction:
$0.00
 
Rent/royalty/partnership/estate (Schedule E):
$0.00
 
Total income:
$250,950.00
 
Total income per computer:
$250,950.00"""

    page2 = """Page 2/6
Adjustments to Income
 
Educator expenses:
$0.00
 
Educator expenses per computer:
$0.00
 
Health Savings Account deduction:
$0.00
 
Health Savings Account deduction per computer:
$0.00
 
Self-employment tax deduction:
$0.00
 
Self-employment tax deduction per computer:
$0.00
 
Keogh/SEP contribution deduction:
$0.00
 
Self-employment health insurance deduction:
$0.00
 
Early withdrawal of savings penalty:
$0.00
 
Alimony paid:
$0.00
 
IRA deduction:
$0.00
 
IRA deduction per computer:
$0.00
 
Student loan interest deduction:
$0.00
 
Student loan interest deduction per computer:
$0.00
 
Total adjustments:
$0.00
 
Total adjustments per computer:
$0.00
 
Adjusted gross income:
$250,950.00
 
Adjusted gross income per computer:
$250,950.00
Tax and Credits
 
Standard deduction per computer:
$12,550.00
 
Taxable income:
$238,400.00
 
Taxable income per computer:
$238,400.00
 
Tentative tax:
$55,000.00
 
Tentative tax per computer:
$55,000.00
 
Foreign tax credit:
$100.00
 
Foreign tax credit per computer:
$100.00
 
Total credits:
$100.00
 
Total credits per computer:
$100.00
 
Income tax after credits per computer:
$54,900.00"""

    page3 = """Page 3/6
Other Taxes
 
Self employment tax:
$0.00
 
Self employment tax per computer:
$0.00
 
Tax on qualified plans Form 5329 (PR):
$0.00
 
Tax on qualified plans Form 5329 per computer:
$0.00
 
Total other taxes per computer:
$1,500.00
 
Total other taxes:
$1,500.00
 
Total assessment per computer:
$56,400.00
 
Total tax liability taxpayer figures:
$56,400.00
 
Total tax liability taxpayer figures per computer:
$56,400.00
Payments
 
Federal income tax withheld:
$45,000.00
 
Estimated tax payments:
$10,000.00
 
Total payments:
$55,000.00
 
Total payments per computer:
$55,000.00
Refund or Amount Owed
 
Amount you owe:
$1,400.00
 
Estimated tax penalty:
$0.00"""

    page4 = """Page 4/6
Interest and Dividends
 
Gross Schedule B interest:
$250.00
 
Taxable interest income:
$250.00
 
Gross Schedule B dividends:
$1,200.00
 
Dividend income:
$1,200.00
 
Foreign accounts indicator:
No
Schedule D - Capital Gains and Losses
Short Term Capital Gains and Losses
 
Short term basis no adjustments sale amount:
$5,000.00
 
Short term basis no adjustments cost amount:
$4,500.00
 
Net short-term gain/loss:
$500.00
Long Term Capital Gains and Losses
 
Net long-term gain/loss:
$0.00"""

    # The key page - Form 8606 section
    # Scenario: $18,000 basis (3 years x $6,000 nondeductible contributions)
    # Converted $99,000 from trad IRA. Total IRA value was ~$105,000 at year end + distributions.
    # Pro-rata: basis_ratio = 18,000 / (6,000 FMV_end + 99,000 distributions) = 18,000/105,000 ≈ 0.1714
    # Non-taxable = 99,000 * 0.1714 ≈ 16,971 → taxable = 99,000 - 16,971 = 82,029
    # basis_used = 16,971, basis_end = 18,000 - 16,971 = 1,029... 
    # Actually let's keep it simpler: non_taxable from 1040 = 99,000 - 82,029 = 16,971
    # The 8606 "Taxable nondeductible contributions" field is actually line 1 = current year nondeductible
    # Let me match real IRS transcript field names exactly.
    page5 = """Page 5/6
Form 8606 - Nondeductible IRAs (Occurrence #: 1)
 
Spouse indicator:
Non-joint taxpayer
 
Taxable nondeductible contributions:
$6,000.00
 
Total amount IRA converted to Roth IRA:
$99,000.00
 
IRA basis before conversion:
$18,000.00
 
Taxable amount of conversion:
$82,029.00
 
Roth IRA basis before conversion:
$0.00
 
Traditional, separate and simple IRA distributions:
$99,000.00
Form 8959 - Additional Medicare Tax
 
Medicare wages:
$150,000.00
 
Unreported tips:
$0.00
 
Additional Medicare Tax on Medicare wages:
$0.00
 
Additional Medicare Tax on Medicare wages per computer:
$0.00
 
Total Additional Medicare Tax:
$0.00"""

    page6 = """Page 6/6
Form 8960 - Net Investment Income Tax - Individuals, Estates, and Trusts
 
Taxable interest amount:
$250.00
 
Ordinary dividends:
$1,200.00
 
Total investment income:
$1,450.00
 
Total investment income per computer:
$1,450.00
 
Modified adjusted gross income:
$250,950.00
 
Net investment income tax for individuals:
$0.00
 
Net investment income tax for individuals per computer:
$0.00
This Product Contains Sensitive Taxpayer Data"""

    _write_transcript_pdf(
        "fixtures/2021_transcript_with_8606.pdf",
        [page1, page2, page3, page4, page5, page6],
        6,
    )


def generate_2024_no_ira_activity() -> None:
    """Generate a 2024 transcript with NO IRA activity and no Form 8606.

    Scenario: High earner, married filing jointly, no IRA distributions or
    contributions this year. Just W-2 income.
    """
    page1 = """Page 1/5
This Product Contains Sensitive Taxpayer Data
Form 1040 Tax Return Transcript
 
Request Date:
03-15-2026
 
Response Date:
03-15-2026
 
Tracking Number:
100000000002
 
SSN provided:
XXX-XX-1234
 
Report for Tax Period Ending:
12-31-2024
The following items reflect the amount as shown on the return, and the amount as adjusted, if applicable. They do not show subsequent 
activity on the account.
 
SSN:
XXX-XX-1234
 
Spouse SSN:
XXX-XX-5678
 
JANE A DOE & JOHN B DOE
 
100 MAIN ST
 
Filing status:
Married Taxpayer Filing Joint Return
 
Form number:
1040
 
Cycle posted:
20251105
 
Received date:
03-09-2025
 
Payment:
$0.00
 
Exemption number:
02
 
PTIN:
XXX-XX-9999
 
Preparer EIN:
XX-XXX0001
Income
 
Total wages:
$280,000.00
 
Form W-2 wages:
$280,000.00
 
Taxable interest income (Schedule B):
$3,500.00
 
Tax-exempt interest:
$0.00
 
Ordinary dividend income (Schedule B):
$2,800.00
 
Qualified dividends:
$1,500.00
 
Capital gain or loss (Schedule D):
$1,200.00
 
Capital gains or loss (Schedule D) per computer:
$1,200.00
 
Total IRA distributions:
$0.00
 
Taxable IRA distributions:
$0.00
 
Total pensions and annuities:
$0.00
 
Taxable pension/annuity amount:
$0.00
 
Total income:
$287,500.00
 
Total income per computer:
$287,500.00"""

    page2 = """Page 2/5
Adjustments to Income
 
Educator expenses:
$0.00
 
Health Savings Account deduction:
$0.00
 
Health Savings Account deduction per computer:
$0.00
 
Self-employment tax deduction:
$0.00
 
Keogh/SEP contribution deduction:
$0.00
 
IRA deduction:
$0.00
 
IRA deduction per computer:
$0.00
 
Student loan interest deduction:
$0.00
 
Total adjustments:
$0.00
 
Total adjustments per computer:
$0.00
 
Adjusted gross income:
$287,500.00
 
Adjusted gross income per computer:
$287,500.00
Tax and Credits
 
Standard deduction per computer:
$29,200.00
 
Taxable income:
$258,300.00
 
Taxable income per computer:
$258,300.00
 
Tentative tax:
$50,000.00
 
Tentative tax per computer:
$50,000.00
 
Total credits:
$0.00
 
Total credits per computer:
$0.00"""

    page3 = """Page 3/5
Other Taxes
 
Self employment tax:
$0.00
 
Total other taxes:
$2,100.00
 
Total other taxes per computer:
$2,100.00
 
Total assessment per computer:
$52,100.00
 
Total tax liability taxpayer figures:
$52,100.00
 
Total tax liability taxpayer figures per computer:
$52,100.00
Payments
 
Federal income tax withheld:
$60,000.00
 
Estimated tax payments:
$0.00
 
Total payments:
$60,000.00
 
Total payments per computer:
$60,000.00
Refund or Amount Owed
 
Overpayment:
$7,900.00
 
Refund amount:
$7,900.00"""

    page4 = """Page 4/5
Interest and Dividends
 
Gross Schedule B interest:
$3,500.00
 
Taxable interest income:
$3,500.00
 
Gross Schedule B dividends:
$2,800.00
 
Dividend income:
$2,800.00
 
Foreign accounts indicator:
No
Schedule D - Capital Gains and Losses
 
Net short-term gain/loss:
$200.00
 
Net long-term gain/loss:
$1,000.00"""

    page5 = """Page 5/5
Form 8959 - Additional Medicare Tax
 
Medicare wages:
$280,000.00
 
Additional Medicare Tax on Medicare wages:
$900.00
 
Additional Medicare Tax on Medicare wages per computer:
$900.00
 
Total Additional Medicare Tax:
$900.00
Form 8960 - Net Investment Income Tax - Individuals, Estates, and Trusts
 
Total investment income:
$6,300.00
 
Total investment income per computer:
$6,300.00
 
Modified adjusted gross income:
$287,500.00
 
Net investment income tax for individuals:
$1,200.00
 
Net investment income tax for individuals per computer:
$1,200.00
This Product Contains Sensitive Taxpayer Data"""

    _write_transcript_pdf(
        "fixtures/2024_transcript_no_ira.pdf",
        [page1, page2, page3, page4, page5],
        5,
    )


def generate_2023_clean_backdoor() -> None:
    """Generate a 2023 transcript showing a clean backdoor Roth.

    Scenario: Contributed $6,500 nondeductible, immediately converted $6,500.
    No other IRA balance (FMV was just the contribution). Zero basis before,
    $6,500 added, all used in conversion, zero taxable.
    """
    page1 = """Page 1/5
This Product Contains Sensitive Taxpayer Data
Form 1040 Tax Return Transcript
 
Request Date:
03-15-2026
 
Response Date:
03-15-2026
 
Tracking Number:
100000000003
 
SSN provided:
XXX-XX-1234
 
Report for Tax Period Ending:
12-31-2023
The following items reflect the amount as shown on the return, and the amount as adjusted, if applicable. They do not show subsequent 
activity on the account.
 
SSN:
XXX-XX-1234
 
Spouse SSN:
 
JANE A DOE
 
100 MAIN ST
 
Filing status:
Single Taxpayer
 
Form number:
1040
 
Cycle posted:
20241405
 
Received date:
04-10-2024
 
Payment:
$0.00
 
Exemption number:
01
 
PTIN:
XXX-XX-9999
 
Preparer EIN:
XX-XXX0001
Income
 
Wages, salaries, tips, etc:
$175,000.00
 
Taxable interest income (Schedule B):
$400.00
 
Ordinary dividend income (Schedule B):
$1,500.00
 
Qualified dividends:
$900.00
 
Capital gain or loss (Schedule D):
$0.00
 
Total IRA distributions:
$6,500.00
 
Taxable IRA distributions:
$0.00
 
Total pensions and annuities:
$0.00
 
Total income:
$176,900.00
 
Total income per computer:
$176,900.00"""

    page2 = """Page 2/5
Adjustments to Income
 
Educator expenses:
$0.00
 
Health Savings Account deduction:
$0.00
 
IRA deduction:
$0.00
 
IRA deduction per computer:
$0.00
 
Student loan interest deduction:
$0.00
 
Total adjustments:
$0.00
 
Total adjustments per computer:
$0.00
 
Adjusted gross income:
$176,900.00
 
Adjusted gross income per computer:
$176,900.00
Tax and Credits
 
Standard deduction per computer:
$13,850.00
 
Taxable income:
$163,050.00
 
Taxable income per computer:
$163,050.00
 
Tentative tax:
$33,500.00
 
Tentative tax per computer:
$33,500.00
 
Total credits:
$0.00
 
Total credits per computer:
$0.00"""

    page3 = """Page 3/5
Other Taxes
 
Self employment tax:
$0.00
 
Total other taxes:
$0.00
 
Total assessment per computer:
$33,500.00
 
Total tax liability taxpayer figures:
$33,500.00
 
Total tax liability taxpayer figures per computer:
$33,500.00
Payments
 
Federal income tax withheld:
$38,000.00
 
Total payments:
$38,000.00
 
Total payments per computer:
$38,000.00
Refund or Amount Owed
 
Overpayment:
$4,500.00
 
Refund amount:
$4,500.00"""

    # Clean backdoor: $6,500 contributed nondeductible, $6,500 converted, $0 taxable
    page4 = """Page 4/5
Form 8606 - Nondeductible IRAs (Occurrence #: 1)
 
Spouse indicator:
Non-joint taxpayer
 
Taxable nondeductible contributions:
$6,500.00
 
Total amount IRA converted to Roth IRA:
$6,500.00
 
IRA basis before conversion:
$6,500.00
 
Taxable amount of conversion:
$0.00
 
Roth IRA basis before conversion:
$0.00
 
Traditional, separate and simple IRA distributions:
$6,500.00"""

    page5 = """Page 5/5
Form 8959 - Additional Medicare Tax
 
Medicare wages:
$175,000.00
 
Additional Medicare Tax on Medicare wages:
$0.00
 
Total Additional Medicare Tax:
$0.00
Form 8960 - Net Investment Income Tax - Individuals, Estates, and Trusts
 
Total investment income:
$1,900.00
 
Modified adjusted gross income:
$176,900.00
 
Net investment income tax for individuals:
$0.00
This Product Contains Sensitive Taxpayer Data"""

    _write_transcript_pdf(
        "fixtures/2023_transcript_clean_backdoor.pdf",
        [page1, page2, page3, page4, page5],
        5,
    )


def generate_2020_contribution_only() -> None:
    """Generate a 2020 transcript with nondeductible contribution but no conversion.

    Scenario: Contributed $6,000 nondeductible to Traditional IRA. No conversion.
    Building basis for a future backdoor Roth.
    """
    page1 = """Page 1/4
This Product Contains Sensitive Taxpayer Data
Form 1040 Tax Return Transcript
 
Request Date:
03-15-2026
 
Response Date:
03-15-2026
 
Tracking Number:
100000000004
 
SSN provided:
XXX-XX-1234
 
Report for Tax Period Ending:
12-31-2020
The following items reflect the amount as shown on the return, and the amount as adjusted, if applicable. They do not show subsequent 
activity on the account.
 
SSN:
XXX-XX-1234
 
Spouse SSN:
 
JANE A DOE
 
100 MAIN ST
 
Filing status:
Single Taxpayer
 
Form number:
1040
 
Cycle posted:
20211505
 
Received date:
05-17-2021
 
Payment:
$0.00
 
Exemption number:
01
 
PTIN:
XXX-XX-9999
 
Preparer EIN:
XX-XXX0001
Income
 
Wages, salaries, tips, etc:
$140,000.00
 
Taxable interest income (Schedule B):
$180.00
 
Ordinary dividend income (Schedule B):
$950.00
 
Qualified dividends:
$600.00
 
Capital gain or loss (Schedule D):
$0.00
 
Total IRA distributions:
$0.00
 
Taxable IRA distributions:
$0.00
 
Total pensions and annuities:
$0.00
 
Total income:
$141,130.00
 
Total income per computer:
$141,130.00"""

    page2 = """Page 2/4
Adjustments to Income
 
IRA deduction:
$0.00
 
IRA deduction per computer:
$0.00
 
Total adjustments:
$0.00
 
Adjusted gross income:
$141,130.00
 
Adjusted gross income per computer:
$141,130.00
Tax and Credits
 
Standard deduction per computer:
$12,400.00
 
Taxable income:
$128,730.00
 
Taxable income per computer:
$128,730.00
 
Tentative tax:
$27,000.00
 
Total credits:
$0.00
Payments
 
Federal income tax withheld:
$30,000.00
 
Total payments:
$30,000.00
Refund or Amount Owed
 
Overpayment:
$3,000.00"""

    page3 = """Page 3/4
Form 8606 - Nondeductible IRAs (Occurrence #: 1)
 
Spouse indicator:
Non-joint taxpayer
 
Taxable nondeductible contributions:
$6,000.00
 
Total amount IRA converted to Roth IRA:
$0.00
 
IRA basis before conversion:
$6,000.00
 
Taxable amount of conversion:
$0.00
 
Roth IRA basis before conversion:
$0.00
 
Traditional, separate and simple IRA distributions:
$0.00"""

    page4 = """Page 4/4
Form 8959 - Additional Medicare Tax
 
Medicare wages:
$140,000.00
 
Additional Medicare Tax on Medicare wages:
$0.00
 
Total Additional Medicare Tax:
$0.00
This Product Contains Sensitive Taxpayer Data"""

    _write_transcript_pdf(
        "fixtures/2020_transcript_contribution_only.pdf",
        [page1, page2, page3, page4],
        4,
    )


if __name__ == "__main__":
    print("Generating synthetic IRS Tax Return Transcript fixtures...")
    generate_2020_contribution_only()
    generate_2021_with_distributions()
    generate_2023_clean_backdoor()
    generate_2024_no_ira_activity()
    print("Done!")
