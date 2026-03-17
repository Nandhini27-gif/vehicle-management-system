import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sqlite3
import pandas as pd
import random
from datetime import datetime
from fpdf import FPDF
import os

if "role" not in st.session_state:
    st.session_state.role = None
st.set_page_config(page_title="Vehicle Management System",layout="wide")
st_autorefresh(interval=5000,key='refresh')

# ---------------- UI STYLE ----------------

st.markdown("""
<style>

.stApp{
background-image:url("https://images.unsplash.com/photo-1503376780353-7e6692767b70");
background-size:cover;
background-position:center;
}

.stApp::before{
content:"";
position:fixed;
top:0;
left:0;
width:100%;
height:100%;
background:rgba(0,0,0,0.55);
z-index:-1;
}

.title{
font-size:60px;
font-weight:900;
color:white;
text-align:center;
text-shadow:3px 3px 12px black;
margin-bottom:30px;
}

h1,h2,h3{
color:white !important;
font-weight:900 !important;
text-shadow:2px 2px 8px black;
}

label{
color:white !important;
font-weight:900 !important;
font-size:18px !important;
text-shadow:1px 1px 5px black;
}

input{
color:black !important;
font-weight:700 !important;
}

.stButton>button{
background:#7b2cff;
color:white;
font-weight:900;
border-radius:10px;
}

</style>
""",unsafe_allow_html=True)

# ---------------- DATABASE ----------------

conn=sqlite3.connect("vehicle.db",check_same_thread=False)
cur=conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS mechanic(
id INTEGER PRIMARY KEY,
name TEXT,
specialization TEXT,
password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS service(
id INTEGER PRIMARY KEY AUTOINCREMENT,
customer TEXT,
phone TEXT,
vehicle_no TEXT,
vehicle_type TEXT,
repair TEXT,
price INTEGER,
status TEXT,
mechanic_id INTEGER,
date TEXT,
invoice TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS stock(
part TEXT PRIMARY KEY,
qty INTEGER
)
""")

# DEFAULT STOCK

stocks=[
("Brake Pad",10),
("Engine Oil",15),
("Air Filter",7),
("Clutch Plate",5),
("Battery",3)
]

for s in stocks:
    cur.execute("INSERT OR IGNORE INTO stock VALUES(?,?)",s)

conn.commit()

# ---------------- REPAIR TYPES ----------------

repairs={

"Bike":{
"Brake Pad":500,
"Engine Oil":700,
"Bike General Check":300
},

"Car":{
"Oil Change":2000,
"Brake Service":1800,
"Car General Check":600
},

"Auto":{
"Engine Repair":1500,
"Auto General Check":400
},

"Scooty":{
"Scooty Brake":450,
"Scooty General Check":250
},

"Truck":{
"Truck Engine":3000,
"Truck General Check":1000
}

}

# ---------------- SESSION ----------------

if "role" not in st.session_state:
    st.session_state.role=None

def logout():
    st.session_state.clear()
    st.rerun()

# ---------------- LOGIN ----------------

def login():

    st.markdown("<div class='title'>🚗 Vehicle Management System</div>",unsafe_allow_html=True)

    role=st.selectbox("Login As",["Admin","Mechanic","Customer"])

    if role=="Admin":

        aid=st.text_input("Admin ID")
        pwd=st.text_input("Password",type="password")

        if st.button("Login"):

            if aid=="admin" and pwd=="admin123":
                st.session_state.role="admin"
                st.rerun()

    elif role=="Mechanic":

        mid=st.text_input("Mechanic ID")
        pwd=st.text_input("Password",type="password")

        if st.button("Login"):

            cur.execute("SELECT * FROM mechanic WHERE id=? AND password=?",(mid,pwd))
            data=cur.fetchone()

            if data:
                st.session_state.role="mechanic"
                st.session_state.mid=data[0]
                st.session_state.mspec=data[2]
                st.rerun()

    else:

        name=st.text_input("Customer Name")
        phone=st.text_input("Phone Number")

        if st.button("Login"):

            st.session_state.role="customer"
            st.session_state.cname=name
            st.session_state.phone=phone
            st.rerun()

# ---------------- ADMIN DASHBOARD ----------------

def admin_dashboard():

    st.sidebar.title("Admin Menu")

    menu = st.sidebar.radio(
        "Navigation",
        ["Add Mechanic","Mechanic List","Remove Mechanic","Services","Stock","Logout"]
    )

    # ---------------- LOGOUT ----------------

    if menu == "Logout":
        logout()


    # ---------------- ADD MECHANIC ----------------

    if menu == "Add Mechanic":

        st.header("Add Mechanic")

        mid = st.number_input("Mechanic ID",step=1)
        name = st.text_input("Mechanic Name")

        spec = st.selectbox(
            "Specialization",
            ["Bike Specialist","Car Specialist","Auto Specialist","Scooty Specialist","Truck Specialist"]
        )

        pwd = st.text_input("Password",type="password")

        if st.button("Add Mechanic"):

            cur.execute(
                "INSERT INTO mechanic VALUES(?,?,?,?)",
                (mid,name,spec,pwd)
            )

            conn.commit()

            st.success("Mechanic Added Successfully")


    # ---------------- MECHANIC TABLE ----------------

    if menu == "Mechanic List":

        st.header("Mechanic List")

        cur.execute("SELECT * FROM mechanic")

        rows = cur.fetchall()

        if rows:

            df = pd.DataFrame(
                rows,
                columns=["ID","Name","Specialization","Password"]
            )

            st.dataframe(df)

        else:
            st.info("No Mechanics Added Yet")


    # ---------------- REMOVE MECHANIC ----------------

    if menu == "Remove Mechanic":

        st.header("Remove Mechanic")

        rid = st.number_input("Enter Mechanic ID",step=1)

        if st.button("Remove Mechanic"):

            cur.execute(
                "DELETE FROM mechanic WHERE id=?",
                (rid,)
            )

            conn.commit()

            st.success("Mechanic Removed Successfully")


    # ---------------- SERVICE TABLE ----------------

    if menu == "Services":

        st.header("Service Records")

        cur.execute("SELECT * FROM service")

        rows = cur.fetchall()

        df = pd.DataFrame(
            rows,
            columns=[
                "ID","Customer","Phone","Vehicle","Type",
                "Repair","Price","Status","Mechanic","Date","Invoice"
            ]
        )

        st.dataframe(df)


    # ---------------- STOCK ----------------

    if menu == "Stock":

        st.header("Stock Management")

        part = st.text_input("Part Name")
        qty = st.number_input("Quantity",step=1)

        if st.button("Add / Update Stock"):

            cur.execute(
                "INSERT OR REPLACE INTO stock VALUES(?,?)",
                (part,qty)
            )

            conn.commit()

            st.success("Stock Updated")

        cur.execute("SELECT * FROM stock")

        rows = cur.fetchall()

        df = pd.DataFrame(rows,columns=["Part","Quantity"])

        st.dataframe(df)

# ---------------- MECHANIC DASHBOARD ----------------

def mechanic_dashboard():

    st.sidebar.title("Mechanic Menu")

    if st.sidebar.button("Logout"):
        logout()

    vtype = st.session_state.mspec.split()[0]

    # service request fetch
    cur.execute(
        "SELECT * FROM service WHERE mechanic_id=? AND status='Pending'",
        (st.session_state.mid,)
    )

    rows = cur.fetchall()

    if rows:

        st.subheader("Service Requests")

        df = pd.DataFrame(rows, columns=[
            "ID","Customer","Phone","Vehicle","Type",
            "Repair","Price","Status","Mechanic","Date","Invoice"
        ])

        st.dataframe(df)

        for r in rows:

            if st.button(f"Complete Service {r[0]}"):

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                pdf.cell(200,10,"Vehicle Service Invoice",ln=True)
                pdf.cell(200,10,f"Customer: {r[1]}",ln=True)
                pdf.cell(200,10,f"Phone: {r[2]}",ln=True)
                pdf.cell(200,10,f"Vehicle: {r[3]}",ln=True)
                pdf.cell(200,10,f"Repair: {r[5]}",ln=True)
                pdf.cell(200,10,f"Price: {r[6]}",ln=True)

                file = f"invoice_{r[0]}.pdf"
                pdf.output(file)

                cur.execute(
                    "UPDATE service SET status='Completed',invoice=? WHERE id=?",
                    (file,r[0])
                )

                conn.commit()

                st.success("Service Completed")
                st.rerun()

# ---------------- CUSTOMER DASHBOARD ----------------

def customer_dashboard():

    st.sidebar.title("Customer Menu")

    menu=st.sidebar.radio("Navigation",
    ["Apply Service","My Services","Logout"])

    if menu=="Logout":
        logout()

    if menu=="Apply Service":

        vehicle=st.text_input("Vehicle Number")

        vtype=st.selectbox("Vehicle Type",list(repairs.keys()))
        repair=st.selectbox("Repair Type",list(repairs[vtype].keys()))

        price=repairs[vtype][repair]

        st.info(f"Estimated Price ₹{price}")

        if st.button("Apply Service"):

            phone=st.session_state.phone
            spec=vtype+" Specialist"

            cur.execute("SELECT id FROM mechanic WHERE specialization=?",(spec,))
            mechs=cur.fetchall()

            mech_id=None

            if mechs:
                mech_id=random.choice(mechs)[0]

            cur.execute("""
            INSERT INTO service
            (customer,phone,vehicle_no,vehicle_type,repair,price,status,mechanic_id,date)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,(st.session_state.cname,
            phone,
            vehicle,
            vtype,
            repair,
            price,
            "Pending",
            mech_id,
            datetime.now()))

            conn.commit()

            st.success("Service Requested")

    if menu=="My Services":

        cur.execute("SELECT * FROM service WHERE phone=?",(st.session_state.phone,))
        rows=cur.fetchall()

        df=pd.DataFrame(rows,columns=[
        "ID","Customer","Phone","Vehicle","Type",
        "Repair","Price","Status","Mechanic","Date","Invoice"
        ])

        st.dataframe(df)

        completed=[r for r in rows if r[7]=="Completed"]

        # 🔊 Notification Sound
        if len(completed) > 0:

            sound = """
            <audio autoplay>
            <source src="https://actions.google.com/sounds/v1/cartoon/wood_plank_flicks.ogg">
            </audio>
            """

            st.markdown(sound, unsafe_allow_html=True)

        st.sidebar.markdown(f"🔔 Notifications ({len(completed)})")

        for r in completed:

            st.success(f"Vehicle {r[3]} service completed")

            if r[10] and os.path.exists(r[10]):

                with open(r[10],"rb") as f:

                    st.download_button(
                    "Download Invoice",
                    data=f.read(),
                    file_name=r[10],
                    mime="application/pdf"
                    )
# ---------------- ROUTER ----------------

if st.session_state.role is None:
    login()

elif st.session_state.role == "admin":
    admin_dashboard()

elif st.session_state.role == "mechanic":
    mechanic_dashboard()

elif st.session_state.role == "customer":
    customer_dashboard()