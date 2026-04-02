import streamlit as st
import pandas as pd
import io
from datetime import date
from database import create_tables, get_connection

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Tea Point Tracker", layout="wide")

create_tables()
conn = get_connection()

st.markdown(
    "<h1 style='text-align: center;'>☕ Finance Tracker</h1>",
    unsafe_allow_html=True
)

st.divider()

# =================================================
# 🔔 DISPLAY FLASH MESSAGE
# =================================================
import time

if st.session_state.get("flash_message"):
    st.success(st.session_state.flash_message)
    time.sleep(1)  # ⭐ keeps visible ~1 sec
    st.session_state.flash_message = None

st.markdown(
    """
    <style>
    /* ===== FORCE CENTER ALIGN FOR STREAMLIT DATA EDITOR ===== */

    /* Body cells */
    div[data-testid="stDataEditor"] [role="gridcell"] {
        justify-content: center !important;
        text-align: center !important;
    }

    /* Header cells */
    div[data-testid="stDataEditor"] [role="columnheader"] {
        justify-content: center !important;
        text-align: center !important;
    }

    /* Fallback for dataframe */
    div[data-testid="stDataFrame"] td, 
    div[data-testid="stDataFrame"] th {
        text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =================================================
# 🔄 SESSION STATE INIT
# =================================================
if "from_date" not in st.session_state:
    st.session_state.from_date = date.today()

if "to_date" not in st.session_state:
    st.session_state.to_date = date.today()

if "filter_manual" not in st.session_state:
    st.session_state.filter_manual = False
    
if "flash_message" not in st.session_state:
    st.session_state.flash_message = None

if "sale_success" not in st.session_state:
    st.session_state.sale_success = None

if "expense_success" not in st.session_state:
    st.session_state.expense_success = None

# =================================================
# 🔄 RESET FLAGS
# =================================================
if "reset_sale_flag" not in st.session_state:
    st.session_state.reset_sale_flag = False

if "reset_exp_flag" not in st.session_state:
    st.session_state.reset_exp_flag = False

# =================================================
# 🔔 SUCCESS MESSAGE STATE
# =================================================
if "flash_message" not in st.session_state:
    st.session_state.flash_message = None

# =================================================
# 📅 BUSINESS DATE (GLOBAL)
# =================================================
st.header("🗓️ Business Date")

business_date = st.date_input(
    "Select Working Date",
    value=date.today(),
    key="business_date"
)

# ⭐ AUTO SYNC (only if user has not manually changed filter)
if "last_business_date" not in st.session_state:
    st.session_state.last_business_date = business_date

# ⭐ Detect business date change
if st.session_state.last_business_date != business_date:
    # Reset manual override when business date changes
    st.session_state.filter_manual = False

    # Update filters to new business date
    st.session_state.from_date = business_date
    st.session_state.to_date = business_date

    st.session_state.last_business_date = business_date

if not st.session_state.filter_manual:
    st.session_state.from_date = business_date
    st.session_state.to_date = business_date

st.divider()

# ---------------- DELETE FUNCTION ----------------
def delete_record(table, record_id):
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
    conn.commit()


# =================================================
# 🔄 APPLY FORM RESETS SAFELY
# =================================================
if st.session_state.reset_sale_flag:
    st.session_state.sale_amount = 0.0
    st.session_state.payment_type = "Counter Cash"
    st.session_state.sale_notes = ""
    st.session_state.reset_sale_flag = False

if st.session_state.reset_exp_flag:
    st.session_state.exp_amount = 0.0
    st.session_state.category = "Milk"
    st.session_state.exp_notes = ""
    st.session_state.reset_exp_flag = False

# =================================================
#  DAILY ENTRY (SIDE BY SIDE)
# =================================================

st.header("Daily Entry")

col_sale, col_exp = st.columns(2)

# ================= LEFT — SALE =================
with col_sale:
    st.subheader(" Add Daily Sale")

    sale_amount = st.number_input(
        "Sale Amount",
        min_value=0.0,
        step=1.0,
        key="sale_amount"
    )

    payment_type = st.selectbox(
        "Payment Type",
        ["Counter Cash", "Paytm", "UPI"],
        key="payment_type"
    )

    sale_notes = st.text_input("Sale Notes", key="sale_notes")

    if st.button("Add Sale", use_container_width=True):
        if sale_amount <= 0:
            st.warning("⚠️ Sale amount must be greater than zero.")
        elif business_date > date.today():
            st.warning("⚠️ Cannot add sales for future dates.")
        else:
            conn.execute(
                "INSERT INTO sales(date, amount, payment_type, notes) VALUES (?, ?, ?, ?)",
                (str(business_date), sale_amount, payment_type, sale_notes),
            )
            conn.commit()
            # ⭐ build dynamic message
            st.session_state.sale_success = {
                "msg": f"✅ ₹{sale_amount:.2f} via {payment_type} successfully added",
                "time": pd.Timestamp.now()
            }

            st.session_state.reset_sale_flag = True
            st.rerun()

    # ================= SALE SUCCESS MESSAGE =================
    if st.session_state.sale_success:
        elapsed = (pd.Timestamp.now() - st.session_state.sale_success["time"]).total_seconds()

        if elapsed < 1.2:
            st.success(st.session_state.sale_success["msg"])
        else:
            st.session_state.sale_success = None

# ================= RIGHT — EXPENSE =================
with col_exp:
    st.subheader(" Add Daily Expense")

    exp_amount = st.number_input(
        "Expense Amount",
        min_value=0.0,
        step=1.0,
        key="exp_amount"
    )

    category = st.selectbox(
        "Category",
        ["Milk", "water bottles", "Sugar", "Honey", "Tea-glasses", "Biscuits" , "Petrol" , "Tea packing covers", "Other"],
        key="category"
    )

    exp_notes = st.text_input("Expense Notes", key="exp_notes")

    if st.button("Add Expense", use_container_width=True):
        if exp_amount <= 0:
            st.warning("⚠️ Expense amount must be greater than zero.")
        elif business_date > date.today():
            st.warning("⚠️ Cannot add expense for future dates.")
        else:
            conn.execute(
                "INSERT INTO expenses(date, amount, category, notes) VALUES (?, ?, ?, ?)",
                (str(business_date), exp_amount, category, exp_notes),
            )
            conn.commit()

            st.session_state.expense_success = {
                "msg": f"✅ ₹{exp_amount:.2f} expense under {category} successfully added",
                "time": pd.Timestamp.now(),
            }

            st.session_state.reset_exp_flag = True
            st.rerun()

    # ================= EXPENSE SUCCESS MESSAGE =================
    if st.session_state.expense_success:
        elapsed = (pd.Timestamp.now() - st.session_state.expense_success["time"]).total_seconds()

        if elapsed < 1.2:
            st.success(st.session_state.expense_success["msg"])
        else:
            st.session_state.expense_success = None

st.divider()

# =================================================
# 📅 FILTER BY DATE RANGE
# =================================================
st.subheader("📅 Filter by Date Range")

colf1, colf2 = st.columns(2)

def mark_manual():
    st.session_state.filter_manual = True

with colf1:
    from_date = st.date_input(
        "From Date",
        key="from_date",
        on_change=mark_manual
    )

with colf2:
    to_date = st.date_input(
        "To Date",
        key="to_date",
        on_change=mark_manual
    )
if from_date > to_date:
    st.error("⚠️ From Date cannot be greater than To Date.")
    st.stop()

# =================================================
# 💼 MONTHLY OVERHEADS
# =================================================
st.subheader("💼 Monthly Fixed Costs")

c1, c2, c3 = st.columns(3)

with c1:
    worker1 = st.number_input("Employee 1 Salary (Monthly)", min_value=0.0, step=100.0)

with c2:
    worker2 = st.number_input("Employee 2 Salary (Monthly)", min_value=0.0, step=100.0)

with c3:
    worker3 = st.number_input("Employee 3 Salary (Monthly)", min_value=0.0, step=100.0)

c4, c5, c6 = st.columns(3)

with c4:
    monthly_rent = st.number_input("Monthly Rent", min_value=0.0, step=100.0)

with c5:
    current_bill = st.number_input("Monthly Current Bill", min_value=0.0, step=100.0)

with c6:
    int_Capital = st.number_input("Monthly Interest on capital", min_value=0.0, step=100.0)

material_cost = st.number_input(
    "Monthly Material Cost",
    min_value=0.0,
    step=100.0,
    help="Fixed monthly material overhead (if any)"
)

# =================================================
# LOAD FILTERED DATA
# =================================================
sales_query = """
SELECT * FROM sales
WHERE date BETWEEN ? AND ?
"""
expense_query = """
SELECT * FROM expenses
WHERE date BETWEEN ? AND ?
"""

sales_df = pd.read_sql(
    sales_query, conn, params=(str(from_date), str(to_date))
)

expense_df = pd.read_sql(
    expense_query, conn, params=(str(from_date), str(to_date))
)

# =================================================
# 📅 CALCULATE DAYS IN FILTER RANGE
# =================================================
from datetime import datetime

days_selected = (to_date - from_date).days + 1
days_selected = max(days_selected, 1)

# Days in current month (approx for allocation)
import calendar
days_in_month = calendar.monthrange(from_date.year, from_date.month)[1]

# =================================================
# 💰 DAILY OVERHEAD CALCULATION
# =================================================
total_monthly_salary = worker1 + worker2 + worker3
total_monthly_fixed = (
    total_monthly_salary
    + monthly_rent
    + current_bill
    + material_cost
    + int_Capital
)

daily_fixed_cost = total_monthly_fixed / days_in_month if days_in_month else 0
range_fixed_cost = daily_fixed_cost * days_selected

# =================================================
# 📊 DASHBOARD
# =================================================
st.subheader("📈 Summary for Selected Period")

total_sales = sales_df["amount"].sum() if not sales_df.empty else 0
total_expenses = expense_df["amount"].sum() if not expense_df.empty else 0
profit = total_sales - total_expenses - range_fixed_cost

c1, c2, c3 = st.columns(3)

c1.metric("💰 Total Sales", f"₹{total_sales:.2f}")
c2.metric("💸 Total Expenses", f"₹{total_expenses:.2f}")
c3.metric("📈 Net Profit", f"₹{profit:.2f}")
st.caption(
    f"🧮 Fixed cost deducted for {days_selected} day(s): ₹{range_fixed_cost:.2f} "
    f"(Daily ₹{daily_fixed_cost:.2f})"
)

st.divider()

# =================================================
# 📋 TRANSACTION DETAILS
# =================================================
tab1, tab2 = st.tabs(["💰 Sales History", "💸 Expense History"])

# ---------------- SALES TAB ----------------
with tab1:
    st.subheader("Sales Records")

    if not sales_df.empty:
        sales_view = (
            sales_df.sort_values(by="date", ascending=True)
            .reset_index(drop=True)
        )

        sales_view.insert(0, "S.No", sales_view.index + 1)
        sales_view["Delete"] = False

        edited_sales = st.data_editor(
            sales_view,
            use_container_width=True,
            hide_index=True,
            key="sales_editor",
            column_config={
                "id": None,

                "S.No": st.column_config.NumberColumn(
                    "S.No", width="small", disabled=True
                ),

                "date": st.column_config.TextColumn(
                    "Date", width="medium", disabled=True
                ),

                "amount": st.column_config.NumberColumn(
                    "Amount", width="medium", disabled=False
                ),

                "payment_type": st.column_config.SelectboxColumn(
                    "Payment Type",
                    options=["Counter Cash", "Paytm", "UPI"],
                    width="medium",
                    disabled=False,
                ),

                "notes": st.column_config.TextColumn(
                    "Notes", width="large", disabled=False
                ),

                "Delete": st.column_config.CheckboxColumn(
                    "Delete", width="small"
                ),
            },
        )

        
        rows_to_delete = edited_sales[edited_sales["Delete"] == True]

        if not rows_to_delete.empty:
            for _, row in rows_to_delete.iterrows():
                delete_record("sales", row["id"])
            st.success("✅ Selected sales deleted.")
            st.rerun()
    else:
        st.info("No sales found for selected period.")

# ---------------- EXPENSE TAB ----------------
with tab2:
    st.subheader("Expense Records")

    if not expense_df.empty:
        expense_view = (
            expense_df.sort_values(by="date", ascending=True)
            .reset_index(drop=True)
        )

        expense_view.insert(0, "S.No", expense_view.index + 1)
        expense_view["Delete"] = False

        edited_exp = st.data_editor(
            expense_view,
            use_container_width=True,
            hide_index=True,
            key="expense_editor",
            column_config={
                "id": None,

                "S.No": st.column_config.NumberColumn(
                    "S.No", width="small", disabled=True
                ),

                "date": st.column_config.TextColumn(
                    "Date", width="medium", disabled=True
                ),

                "amount": st.column_config.NumberColumn(
                    "Amount", width="medium", disabled=False
                ),

                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=[
                        "Milk",
                        "water bottles",
                        "Sugar",
                        "Honey",
                        "Tea-glasses",
                        "Biscuits",
                        "Petrol",
                        "Tea packing covers",
                        "Other",
                    ],
                    width="medium",
                    disabled=False,
                ),

                "notes": st.column_config.TextColumn(
                    "Notes", width="large", disabled=False
                ),

                "Delete": st.column_config.CheckboxColumn(
                    "Delete", width="small"
                ),
            },
        )
        
        rows_to_delete = edited_exp[edited_exp["Delete"] == True]

        if not rows_to_delete.empty:
            for _, row in rows_to_delete.iterrows():
                delete_record("expenses", row["id"])
            st.success("✅ Selected expenses deleted.")
            st.rerun()
    else:
        st.info("No expenses found for selected period.")

# =================================================
# 📋 Download Excel Report
# =================================================

def convert_to_excel(sales_df, expense_df):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sales_df.to_excel(writer, sheet_name='Sales', index=False)
        expense_df.to_excel(writer, sheet_name='Expenses', index=False)

    return output.getvalue()


excel_data = convert_to_excel(sales_df, expense_df)

st.download_button(
    label="📥 Download Report (Excel)",
    data=excel_data,
    file_name="tea_point_report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
