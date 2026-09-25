import streamlit as st
import pandas as pd
import json
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


st.set_page_config(page_title="Pharmacy Stock System", layout="wide", page_icon="💊")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

:root {
    --teal: #2A9D8F;
    --teal-dark: #21867A;
    --navy: #264653;
    --bg-soft: #F7FAF9;
    --amber: #E9C46A;
    --red: #E76F51;
}

.stApp {
    background-color: var(--bg-soft);
}

h1, h2, h3 {
    color: var(--navy) !important;
    font-weight: 700 !important;
}

/* عنوان التطبيق الرئيسي */
h1 {
    padding-bottom: 0.3rem;
    border-bottom: 3px solid var(--teal);
    display: inline-block;
}

/* الأزرار */
.stButton > button {
    background-color: var(--teal);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1.2rem;
    font-weight: 600;
    transition: background-color 0.15s ease;
}
.stButton > button:hover {
    background-color: var(--teal-dark);
    color: white;
}

/* زرار التحميل */
.stDownloadButton > button {
    background-color: var(--navy);
    color: white;
    border-radius: 8px;
    font-weight: 600;
}

/* التابات */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
}
.stTabs [data-baseweb="tab"] {
    background-color: white;
    border-radius: 8px 8px 0 0;
    padding: 10px 16px;
    font-weight: 600;
    color: var(--navy);
}
.stTabs [aria-selected="true"] {
    background-color: var(--teal) !important;
    color: white !important;
}

/* الجداول */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #E3E9E8;
}

/* الخانات */
input, textarea {
    border-radius: 8px !important;
}

/* رسائل النجاح/الخطأ/التحذير - حواف ناعمة */
.stAlert {
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


# ------------------ تحميل وحفظ المخزون ------------------
def load_stock():
    try:
        with open("pharmacy_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "Panadol": {"quantity": 50, "price": 12.5, "barcode": "1001"},
            "Augmentin": {"quantity": 5, "price": 45.0, "barcode": "1002"},
            "Brufen": {"quantity": 0, "price": 20.0, "barcode": "1003"}
        }


def save_stock():
    with open("pharmacy_data.json", "w") as file:
        json.dump(st.session_state.pharmacy_stock, file)


# ------------------ تحميل وحفظ سجل العمليات ------------------
def load_history():
    try:
        with open("sales_history.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_history():
    with open("sales_history.json", "w") as file:
        json.dump(st.session_state.history, file)


def record_transaction(transaction_type, details, total=None):
    entry = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": transaction_type,
        "details": details,
        "total": total
    }
    st.session_state.history.append(entry)
    save_history()


def find_by_barcode(barcode):
    for name, item in st.session_state.pharmacy_stock.items():
        if item.get("barcode", "") == barcode:
            return name
    return None


# ------------------ توليد فاتورة PDF ------------------
def generate_invoice_pdf(cart_items, total, invoice_number):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Pharmacy Invoice", styles["Title"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Invoice No: " + str(invoice_number), styles["Normal"]))
    story.append(Paragraph("Date: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), styles["Normal"]))
    story.append(Spacer(1, 12))

    table_data = [["Medicine", "Quantity", "Price", "Subtotal"]]
    for item in cart_items:
        table_data.append([
            item["name"],
            str(item["quantity"]),
            str(item["price"]),
            str(round(item["subtotal"], 2))
        ])
    table_data.append(["", "", "Total:", str(round(total, 2))])

    invoice_table = Table(table_data, colWidths=[180, 80, 80, 80])
    invoice_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
    ]))
    story.append(invoice_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


if "pharmacy_stock" not in st.session_state:
    st.session_state.pharmacy_stock = load_stock()

if "cart" not in st.session_state:
    st.session_state.cart = []

if "history" not in st.session_state:
    st.session_state.history = load_history()

if "last_invoice_pdf" not in st.session_state:
    st.session_state.last_invoice_pdf = None

if "last_invoice_number" not in st.session_state:
    st.session_state.last_invoice_number = None


st.title("💊 Pharmacy Stock System")
st.caption("Track inventory, sell, and manage your pharmacy — all in one place.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📋 Stock", "⚠️ Alerts", "➕ Add Medicine", "🔄 Restock / Return", "🛒 POS (Sell)", "📜 History"]
)

# ------------------ Tab 1: عرض المخزون كجدول ------------------
with tab1:
    st.header("Current Stock")
    if st.session_state.pharmacy_stock:
        df = pd.DataFrame(st.session_state.pharmacy_stock).T
        df.index.name = "Medicine"
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No medicines in stock yet.")

# ------------------ Tab 2: التنبيهات ------------------
with tab2:
    st.header("Stock Alerts")
    has_alert = False
    for name, details in st.session_state.pharmacy_stock.items():
        if details["quantity"] == 0:
            st.error(name + " - Out of stock!")
            has_alert = True
        elif details["quantity"] <= 10:
            st.warning(name + " - Low stock: " + str(details["quantity"]))
            has_alert = True
    if not has_alert:
        st.success("All stock levels are healthy.")

# ------------------ Tab 3: إضافة دواء جديد ------------------
with tab3:
    st.header("Add Medicine")
    new_name = st.text_input("Medicine name")
    new_barcode = st.text_input("Barcode")
    new_quantity = st.number_input("Quantity", min_value=0, step=1)
    new_price = st.number_input("Price", min_value=0.0, step=0.5)

    if st.button("Add Medicine"):
        if new_name == "":
            st.error("Please enter a medicine name.")
        else:
            st.session_state.pharmacy_stock[new_name] = {
                "quantity": new_quantity,
                "price": new_price,
                "barcode": new_barcode
            }
            save_stock()
            record_transaction("Add Medicine", new_name + " (qty: " + str(new_quantity) + ")")
            st.success(new_name + " added successfully.")
            st.rerun()

# ------------------ Tab 4: تحديث يدوي (توريد / ارتجاع) ------------------
with tab4:
    st.header("Restock / Return")
    medicine_names = list(st.session_state.pharmacy_stock.keys())

    if medicine_names:
        selected_medicine = st.selectbox("Select medicine", medicine_names, key="restock_select")
        action = st.radio("Action", ["Restock", "Return"], key="restock_action")
        amount = st.number_input("Amount", min_value=1, step=1, key="restock_amount")

        if st.button("Confirm"):
            st.session_state.pharmacy_stock[selected_medicine]["quantity"] += amount
            save_stock()
            record_transaction(action, selected_medicine + " (qty: " + str(amount) + ")")
            st.success(selected_medicine + " updated. New quantity: " +
                       str(st.session_state.pharmacy_stock[selected_medicine]["quantity"]))
            st.rerun()
    else:
        st.write("No medicines in stock yet.")

# ------------------ Tab 5: نقطة البيع (POS) بسلة كاملة ------------------
with tab5:
    st.header("Point of Sale")

    medicine_names = list(st.session_state.pharmacy_stock.keys())

    if medicine_names:
        st.subheader("Add by Barcode")
        col_bar1, col_bar2 = st.columns([2, 1])
        with col_bar1:
            barcode_input = st.text_input("Scan or enter barcode", key="barcode_input")
        with col_bar2:
            barcode_qty = st.number_input("Qty", min_value=1, step=1, key="barcode_qty")

        if st.button("Add by Barcode"):
            matched_name = find_by_barcode(barcode_input)
            if matched_name is None:
                st.error("No medicine found with this barcode.")
            else:
                available = st.session_state.pharmacy_stock[matched_name]["quantity"]
                if barcode_qty > available:
                    st.error("Not enough stock. Only " + str(available) + " available.")
                else:
                    price = st.session_state.pharmacy_stock[matched_name]["price"]
                    st.session_state.cart.append({
                        "name": matched_name,
                        "quantity": barcode_qty,
                        "price": price,
                        "subtotal": barcode_qty * price
                    })
                    st.success(matched_name + " added to cart.")

        st.divider()

        st.subheader("Add by Name")
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            pos_medicine = st.selectbox("Medicine", medicine_names, key="pos_medicine")
        with col_b:
            available = st.session_state.pharmacy_stock[pos_medicine]["quantity"]
            st.write("Available:", available)
        with col_c:
            pos_qty = st.number_input("Qty", min_value=1, step=1, key="pos_qty")

        if st.button("Add to Cart"):
            available = st.session_state.pharmacy_stock[pos_medicine]["quantity"]
            if pos_qty > available:
                st.error("Not enough stock. Only " + str(available) + " available.")
            else:
                price = st.session_state.pharmacy_stock[pos_medicine]["price"]
                st.session_state.cart.append({
                    "name": pos_medicine,
                    "quantity": pos_qty,
                    "price": price,
                    "subtotal": pos_qty * price
                })
                st.success(pos_medicine + " added to cart.")

    st.divider()

    # ------------- عرض السلة -------------
    st.subheader("Cart")
    if st.session_state.cart:
        cart_df = pd.DataFrame(st.session_state.cart)
        st.dataframe(cart_df, use_container_width=True)

        total = sum(item["subtotal"] for item in st.session_state.cart)
        st.write("**Total:", round(total, 2), "**")

        col_x, col_y = st.columns(2)
        with col_x:
            if st.button("Complete Sale"):
                enough_stock = True
                for item in st.session_state.cart:
                    if item["quantity"] > st.session_state.pharmacy_stock[item["name"]]["quantity"]:
                        enough_stock = False
                        st.error("Not enough stock for " + item["name"])

                if enough_stock:
                    items_summary = ", ".join(
                        item["name"] + " x" + str(item["quantity"]) for item in st.session_state.cart
                    )
                    for item in st.session_state.cart:
                        st.session_state.pharmacy_stock[item["name"]]["quantity"] -= item["quantity"]
                    save_stock()

                    invoice_number = datetime.now().strftime("%Y%m%d%H%M%S")
                    pdf_buffer = generate_invoice_pdf(st.session_state.cart, total, invoice_number)
                    st.session_state.last_invoice_pdf = pdf_buffer
                    st.session_state.last_invoice_number = invoice_number

                    record_transaction("Sale", items_summary, round(total, 2))
                    st.session_state.cart = []
                    st.success("Sale completed successfully.")
                    st.rerun()

        with col_y:
            if st.button("Clear Cart"):
                st.session_state.cart = []
                st.rerun()
    else:
        st.write("Cart is empty.")

    # ------------- زرار تحميل آخر فاتورة -------------
    if st.session_state.last_invoice_pdf is not None:
        st.divider()
        st.download_button(
            label="📄 Download Last Invoice (PDF)",
            data=st.session_state.last_invoice_pdf,
            file_name="invoice_" + str(st.session_state.last_invoice_number) + ".pdf",
            mime="application/pdf"
        )

# ------------------ Tab 6: سجل العمليات ------------------
with tab6:
    st.header("Transaction History")
    if st.session_state.history:
        history_df = pd.DataFrame(st.session_state.history)
        history_df = history_df.iloc[::-1]
        st.dataframe(history_df, use_container_width=True)
    else:
        st.write("No transactions recorded yet.")
