"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignment 03. README Step 8 has
# the exact widgets, keys and labels; the tests in tests/test_pipeline.py -k app
# check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster  <- load_employees()                      (fixed; not uploaded)
#   upload  <- st.file_uploader, key="timesheet"     (returns None until chosen)
#   if there is an upload:
#       timesheet <- load_timesheet(upload)
#       payroll   <- build_payroll(timesheet, roster)   one call does all the work
#       the pay period (payroll_date) as a subheader
#       four st.metric cards in st.columns(4) — totals are .sum() on a Series,
#           counts are len() of a boolean-indexed frame
#       st.warning naming the unmatched employee_ids, or st.success if none
#       st.dataframe(payroll) — the lineage table, raw and computed side by side
#       st.download_button, key="download": payroll_export(payroll).to_csv(index=False)
#
# What the page does NOT do: arithmetic on rows, cleaning, merging. If you find
# yourself writing a loop or an apply here, that logic belongs in the package.

import streamlit as st

from payroll import build_payroll, load_employees, load_timesheet, payroll_export


def main() -> None:
    """Render the weekly payroll page and its downloadable provider export."""
    st.title("Salt City Coffee — Weekly Payroll")
    st.write(
        "Upload this week's timesheet to calculate payroll and review the results."
    )

    employees = load_employees()
    uploaded_timesheet = st.file_uploader(
        "Upload the week's timesheet CSV", type="csv", key="timesheet"
    )

    if uploaded_timesheet is None:
        return

    timesheet = load_timesheet(uploaded_timesheet)
    payroll = build_payroll(timesheet, employees)
    payroll_date = str(payroll["payroll_date"].iloc[0])

    st.subheader(f"Pay period: {payroll_date}")
    employees_paid = len(payroll[payroll["pay_type"] != "unmatched"])
    total_hours = payroll["hours_worked"].sum()
    total_gross_pay = payroll["gross_pay"].sum()
    overtime_weeks = len(payroll[payroll["pay_type"] == "overtime"])

    metrics = st.columns(4)
    metrics[0].metric("Employees paid", employees_paid)
    metrics[1].metric("Total hours", f"{total_hours:g}")
    metrics[2].metric("Total gross pay", f"${total_gross_pay:,.2f}")
    metrics[3].metric("Overtime weeks", overtime_weeks)

    unmatched = payroll[payroll["pay_type"] == "unmatched"]
    if len(unmatched):
        employee_ids = ", ".join(unmatched["employee_id"].astype(str).unique())
        st.warning(f"Unmatched employee ID(s): {employee_ids}")
    else:
        st.success("All timesheet employees matched the roster.")

    st.dataframe(payroll)

    export_csv = payroll_export(payroll).to_csv(index=False)
    st.download_button(
        "Download payroll CSV",
        data=export_csv,
        file_name=f"payroll_{payroll_date}.csv",
        mime="text/csv",
        key="download",
    )


if __name__ == "__main__":
    main()
