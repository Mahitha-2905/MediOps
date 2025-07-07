import os
from bson import ObjectId
from flask import Flask, request, render_template, redirect, session
import datetime

import pymongo

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT_LAB_TEST = APP_ROOT + "/static/da"

app = Flask(__name__)
app.secret_key = "da"

Doctor_Appointment = pymongo.MongoClient("mongodb://localhost:27017/")
my_database = Doctor_Appointment["Doctor_Appointment"]
admin_collection = my_database["admin"]
doctor_collection = my_database["doctor"]
time_slots_collection = my_database["slots"]
patient_collection = my_database["patient"]
appointment_collection = my_database["appointment"]
payment_collection = my_database["payment"]
prescription_collection = my_database["prescription"]

query = {}
count = admin_collection.count_documents({})
if count == 0:
    query = {"username": "admin", "password": "admin"}
    admin_collection.insert_one(query)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin_login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/admin_login_action", methods=['post'])
def admin_login_action():
    username = request.form.get("username")
    password = request.form.get("password")
    query = {"username": username, "password": password}
    count = admin_collection.count_documents(query)
    if count > 0:
        admin = admin_collection.find_one(query)
        session["admin_id"] = str(admin['_id'])
        session["role"] = 'admin'
        return redirect("/admin_home")
    else:
        return render_template("message.html", message="Invalid login details")


@app.route("/admin_home")
def admin_home():
    return render_template("admin_home.html")


@app.route("/add_view_doctors")
def add_view_doctors():
    query = {}
    doctors = doctor_collection.find(query)
    doctors = list(doctors)
    return render_template("add_view_doctors.html", doctors=doctors)


@app.route("/add_view_doctor_action", methods=['post'])
def add_view_doctor_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    designation = request.form.get("designation")
    consultationFee = request.form.get("consultationFee")
    specialization = request.form.get("specialization")
    password = request.form.get("password")
    password2 = request.form.get("confirm_password")
    if password != password2:
        return render_template("message_action.html", message="password and confirm password must be same")
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = doctor_collection.count_documents(query)
    if count == 0:
        query = {"name": name, "email": email, "phone": phone, "first_name":first_name,"last_name":last_name,"password": password, "designation": designation, "is_logged": False, "consultationFee": consultationFee, "specialization": specialization}
        doctor_collection.insert_one(query)
        return redirect("/add_view_doctors")
    else:
        return render_template("message.html", message="Duplicate Entry")


@app.route("/edit")
def edit():
    doctor_id = request.args.get("doctor_id")
    doctor = doctor_collection.find_one({"_id": ObjectId(doctor_id)})
    return render_template("/edit.html", doctor_id=doctor_id, doctor=doctor)


@app.route("/edit_doctor_action", methods=['post'])
def edit_doctor_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    doctor_id = request.form.get("doctor_id")
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    designation = request.form.get("designation")
    consultationFee = request.form.get("consultationFee")
    specialization = request.form.get("specialization")
    query = {"$set": {"name": name, "email": email, "phone": phone, "designation": designation,"first_name":first_name,"last_name":last_name,
                      "consultationFee": consultationFee, "specialization": specialization}}
    doctor_collection.update_one({"_id": ObjectId(doctor_id)}, query)
    return redirect("/add_view_doctors")


@app.route("/add_view_doctor_timings_action", methods=['post'])
def add_view_doctor_timings_action():
    doctor_id = session["doctor_id"]
    from_time = request.form.get("from_time")
    from_time2 = datetime.datetime.strptime(from_time, "%H:%M")
    to_time = request.form.get("to_time")
    to_time2 = datetime.datetime.strptime(to_time, "%H:%M")
    doctor = doctor_collection.find_one({})
    doctor_collection.count_documents(doctor)
    day = request.form.get("day")
    query = {"_id": ObjectId(doctor_id), "timings.day": day}
    count = doctor_collection.count_documents(query)
    if count > 0:
        query1 = {"_id": ObjectId(doctor_id)}
        query2 = {"$pull": {"timings": {"day": day}}}
        doctor_collection.update_one(query1, query2)
        # query3 = {"doctor_id": ObjectId(doctor_id)}
        # time_slots_collection.delete_many(query3)

    query = {"$push": {"timings": {"from_time": from_time, "to_time": to_time, "day": day}}}
    doctor_collection.update_one({"_id": ObjectId(doctor_id)}, query)
    doctor_id = ObjectId(session['doctor_id'])
    query = {"doctor_id": ObjectId(doctor_id), "day": day}
    count = time_slots_collection.count_documents(query)
    if count > 0:
        query2 = {"doctor_id": ObjectId(doctor_id), "day": day}
        time_slots_collection.delete_many(query2)
    slot_number = 0
    while from_time2 < to_time2:
        slot_from_time = from_time2
        slot_from_time = slot_from_time.strftime("%H:%M")
        from_time2 = from_time2 + datetime.timedelta(minutes=15)
        slot_to_time = from_time2
        slot_to_time = slot_to_time.strftime("%H:%M")
        slot_number = slot_number + 1
        slot = {"slot_from_time": slot_from_time, "slot_to_time": slot_to_time, "slot_number": slot_number,
                "doctor_id": doctor_id, "day": day}

        time_slots_collection.insert_one(slot)

        next_slot_to_time = from_time2 + datetime.timedelta(minutes=15)
        if next_slot_to_time > to_time2:
            break
    return redirect("/add_view_doctor_timings")




@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/doctor_login")
def doctor_login():
    return render_template("doctor_login.html")


@app.route("/doctor_login_action", methods=['post'])
def doctor_login_action():
    email = request.form.get("email")
    password = request.form.get("password")
    query = {"$or": [{"email": email}, {"name": email}], "password": password}
    count = doctor_collection.count_documents(query)
    if count > 0:
        doctor = doctor_collection.find_one(query)
        if doctor['is_logged']:
            session["doctor_id"] = str(doctor['_id'])
            session["role"] = "doctor"
            return redirect("/doctor_home")

        else:
            session["doctor_id"] = str(doctor['_id'])
            return redirect("/change_password")
    else:
        return render_template("message.html", message="Invalid Login Details")

@app.route("/doctor_home")
def doctor_home():
    return render_template("doctor_home.html")


@app.route("/change_password")
def change_password():
    return render_template("change_password.html")


@app.route("/change_password_action",methods=['post'])
def change_password_action():
    old_password = request.form.get("old_password")
    password = request.form.get("new_password")
    password2 = request.form.get("confirm_password")
    if old_password==password2:
        return render_template("message_action.html", message="old password and new password  same")
    if password != password2:
        return render_template("message_action.html", message="password and confirm password must be same")
    query ={"$set":{"password":password,"is_logged":True}}
    doctor_collection.update_one({"_id":ObjectId(session['doctor_id'])},query)
    session['doctor_id'] = str(session['doctor_id'])
    return redirect("/doctor_home")

@app.route("/add_view_doctor_timings")
def add_view_doctor_timings():
    doctor_id = ObjectId(session['doctor_id'])
    query = {"_id": ObjectId(doctor_id)}
    doctors = doctor_collection.find(query)
    slots = time_slots_collection.find({"doctor_id": ObjectId(session['doctor_id'])})
    slots = list(slots)
    return render_template("add_view_doctor_timings.html", doctors=doctors, slots=slots,formate_time=formate_time,formate_time2=formate_time2)


@app.route("/patient_login")
def patient_login():
    return render_template("patient_login.html")


@app.route("/patient_login_action", methods=['post'])
def patient_login_action():
    user_login = request.form.get("user_login")
    password = request.form.get("password")
    query = {"$or":[{"email": user_login}, {"name": user_login}], "password": password}
    count = patient_collection.count_documents(query)
    if count > 0:
        patient = patient_collection.find_one(query)
        session['patient_id'] = str(patient['_id'])
        session['role'] = "patient"
        return redirect("/patient_home")
    else:
        return render_template("message.html", message="Invalid Login Details")


@app.route("/patient_register")
def patient_register():
    return render_template("patient_register.html")


@app.route("/patient_registration_action", methods=['post'])
def patient_registration_action():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    dob = request.form.get("dob")
    ssn = request.form.get("ssn")
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    zipcode = request.form.get("zipcode")
    city = request.form.get("city")
    password = request.form.get("password")
    password2 = request.form.get("confirm_password")
    if password != password2:
        return render_template("message_action.html", message="password and confirm password must be same")
    query = {"$or": [{"email": email}, {"phone": phone}]}
    count = patient_collection.count_documents(query)
    if count == 0:
        query = {"name": name, "email": email, "password": password, "phone": phone, "zipcode": zipcode, "city": city,"first_name":first_name,"last_name":last_name,"dob":dob,"ssn":ssn}
        patient_collection.insert_one(query)
        return render_template("message.html", message="Patient Registered Successfully")
    else:
        return render_template("message.html", message="Duplicate Entry")


@app.route("/patient_home")
def patient_home():
    return render_template("patient_home.html")


@app.route("/view_doctor")
def view_doctor():
    doctors = doctor_collection.find()
    return render_template("view_doctor.html", doctors=doctors)


@app.route("/doctor_slots")
def doctor_slots():
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    doctor_id = request.args.get("doctor_id")
    query = {"_id": ObjectId(doctor_id)}
    doctor = doctor_collection.find_one(query)
    appointment_date = request.args.get("appointment_date")
    if appointment_date == None:
        date_time = datetime.datetime.today()
        day = date_time.weekday()
        appointment_date = str(date_time.strftime('%Y-%m-%d'))
        appointment_date2 = datetime.date.today()
    else:
        appointment_date2 = appointment_date
        appointment_date = datetime.datetime.strptime(appointment_date, '%Y-%m-%d')
        day = appointment_date.weekday()
        appointment_date = str(appointment_date)
    day = weekdays[day]
    query = {"day": day,"doctor_id": ObjectId(doctor_id)}
    slots = time_slots_collection.find(query)
    return render_template("doctor_slots.html", doctor=doctor, slots=slots, doctor_id=doctor_id,
                           appointment_date=appointment_date, appointment_date2=appointment_date2,
                           is_slot_booked=is_slot_booked)


def is_slot_booked(slot_id, appointment_date):
    print(type(appointment_date))
    appointment_date = appointment_date.strip(" : 0")
    appointment_date = datetime.datetime.strptime(appointment_date,"%Y-%m-%d")
    query = {"slot_id": ObjectId(slot_id), "appointment_date": appointment_date, "status": 'Requested'}
    count = appointment_collection.count_documents(query)
    if count == 0:
        return False
    else:
        return True


@app.route("/description")
def description():
    doctor_id = request.args.get("doctor_id")
    appointment_date = request.args.get("appointment_date")
    slot_id = request.args.get("slot_id")
    return render_template("description.html", doctor_id=doctor_id, appointment_date=appointment_date, slot_id=slot_id)


@app.route("/request_doctor")
def request_doctor():
    doctor_id = request.args.get("doctor_id")
    appointment_date = request.args.get("appointment_date").strip(" :0 ")
    appointment_date = datetime.datetime.strptime(appointment_date, "%Y-%m-%d")
    slot_id = request.args.get("slot_id")
    description = request.args.get("description")
    patient_id = ObjectId(session['patient_id'])
    query = {"doctor_id": ObjectId(doctor_id), "appointment_date": appointment_date, "slot_id": ObjectId(slot_id),
             "description": description, "status": 'Payment Pending', "patient_id": patient_id}
    appointment_collection.insert_one(query)
    return render_template("message_action.html",message="Request sent Successfully")


@app.route("/approve")
def approve():
    appointment_id = request.args.get("appointment_id")
    query1 = {"_id": ObjectId(appointment_id)}
    query2 = {"$set": {"status": "Request Accepted"}}
    appointment_collection.update_one(query1, query2)
    return render_template("message_action.html", message="Request Accepted")


@app.route("/payment")
def payment():
    doctor = doctor_collection.find_one()
    appointment_id = request.args.get("appointment_id")
    return render_template("payment.html", appointment_id=appointment_id,doctor=doctor)


@app.route("/view_bookings")
def view_bookings():

    query = {}
    # appointment_date = request.args.get("appointment_date")
    # if appointment_date == None:
    #     appointment_date = datetime.datetime.now()
    #     appointment_date = appointment_date.strftime("%Y-%m-%d")
    if session['role'] == 'patient':
        patient_id = session["patient_id"]
        query = {"patient_id": ObjectId(patient_id)}
    elif session['role'] == 'doctor':
        doctor_id = session["doctor_id"]

        query = {"doctor_id": ObjectId(doctor_id)}
    elif session['role'] == 'admin':
        query = {}
    appointments = appointment_collection.find(query).sort([('appointment_date', pymongo.ASCENDING)])
    return render_template("view_bookings.html", appointments=appointments,
                           get_doctor_by_doctor_id=get_doctor_by_doctor_id,
                           get_patient_by_patient_id=get_patient_by_patient_id, get_slot_by_slot_id=get_slot_by_slot_id,
                           get_payment_by_appointment_id=get_payment_by_appointment_id)


@app.route("/view_bookings1")
def view_bookings1():
    doctor_id = session["doctor_id"]
    query = {"doctor_id": ObjectId(doctor_id)}
    appointments = appointment_collection.find(query).sort([('appointment_date', pymongo.ASCENDING)])
    appointments = list(appointments)
    return render_template("/view_bookings1.html",appointments=appointments,get_doctor_by_doctor_id=get_doctor_by_doctor_id,get_slot_by_slot_id=get_slot_by_slot_id,get_patient_by_patient_id=get_patient_by_patient_id)


def get_doctor_by_doctor_id(doctor_id):
    query = {"_id": doctor_id}
    doctor = doctor_collection.find_one(query)
    return doctor


def get_patient_by_patient_id(patient_id):
    query = {"_id": patient_id}
    patient = patient_collection.find_one(query)
    return patient


def get_slot_by_slot_id(slot_id):
    query = {"_id": slot_id}
    slot = time_slots_collection.find_one(query)
    return slot


@app.route("/accept")
def accept():
    appointment_id = request.args.get("appointment_id")
    query1 = {"_id": ObjectId(appointment_id)}
    query2 = {"$set": {"status": "Request Accepted"}}
    appointment_collection.update_one(query1, query2)
    return render_template("message_action.html", message="Request Accepted")


def get_payment_by_appointment_id(appointment_id):
    query = {"appointment_id": ObjectId(appointment_id)}
    payment = payment_collection.find_one(query)
    return payment


@app.route("/payment_action", methods=['post'])
def payment_action():
    patient_id = request.form.get("patient_id")
    appointment_id = request.form.get("appointment_id")
    amount = request.form.get("amount")
    card_type = request.form.get("card_type")
    card_number = request.form.get("card_number")
    name_on_card = request.form.get("name_on_card")
    cvv = request.form.get("cvv")
    expiry_date = request.form.get("expiry_date")
    query = {"appointment_id": ObjectId(appointment_id), "patient_id": ObjectId(patient_id), "amount": amount,
             "card_type": card_type, "card_number": card_number, "name_on_card": name_on_card, "cvv": cvv,
             "expiry_date": expiry_date, "status": 'Payment Successfully'}
    payment_collection.insert_one(query)
    query1 = {"_id": ObjectId(appointment_id)}
    query2 = {"$set": {"status": "Appointment Booked"}}
    appointment_collection.update_one(query1, query2)
    return render_template("message_action.html", message="Payment Successfully")


@app.route("/prescription")
def prescription():
    appointment_id = request.args.get("appointment_id")
    return render_template("prescription.html", appointment_id=appointment_id)


@app.route("/submit_prescription")
def submit_prescription():
    appointment_id = request.args.get("appointment_id")
    prescription = request.args.get("prescription")
    # prescribedDate = datetime.datetime.today()
    # prescribedDate2 = datetime.datetime.strptime(str(prescribedDate), "%Y-%m-%d")
    prescriptionValidFromDate = datetime.date.today()
    prescriptionValidToDate = prescriptionValidFromDate + datetime.timedelta(days=15)
    prescriptionValidFromDate2 = datetime.datetime.strptime(str(prescriptionValidFromDate), "%Y-%m-%d")
    prescriptionValidToDate2 = datetime.datetime.strptime(str(prescriptionValidToDate), "%Y-%m-%d")
    query = {"appointment_id": ObjectId(appointment_id), "prescription": prescription,
             "prescriptionValidFromDate": prescriptionValidFromDate2,
             "prescriptionValidToDate": prescriptionValidToDate2}
    prescription_collection.insert_one(query)
    query1 = {"_id": ObjectId(appointment_id)}
    query2 = {"$set": {"status": "Prescribed"}}
    appointment_collection.update_one(query1, query2)
    return render_template("message_action.html", message="Prescription sent Successfully")


@app.route("/view_prescription")
def view_prescription():
    appointment_id = request.args.get("appointment_id")
    prescriptions = prescription_collection.find({"appointment_id": ObjectId(appointment_id)})
    return render_template("view_prescription.html", prescriptions=prescriptions)


@app.route("/reject")
def reject():
    appointment_id = request.args.get("appointment_id")
    return render_template("reject.html", appointment_id=appointment_id)


@app.route("/send_reason")
def send_reason():
    reason = request.args.get("reason")
    appointment_id = request.args.get("appointment_id")
    query1 = {"_id": ObjectId(appointment_id)}
    query2 = {"$set": {"status": 'Request Rejected', "reason": reason}}
    appointment_collection.update_one(query1, query2)
    return render_template("message_action.html", message="Request Rejected")


@app.route("/view_reason")
def view_reason():
    appointment_id = request.args.get("appointment_id")
    appointments = appointment_collection.find()
    return render_template("view_reason.html", appointment_id=appointment_id, appointments=appointments)


@app.route("/view_doctor_slots")
def view_doctor_slots():
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    doctor_id = request.args.get("doctor_id")
    query = {"_id": ObjectId(doctor_id)}
    doctor = doctor_collection.find_one(query)
    slot = time_slots_collection.find({"doctor_id": ObjectId(doctor_id)})
    slot = list(slot)
    day = 0
    available_date = request.args.get("available_date")
    if available_date == None:
        date_time = datetime.datetime.today()
        day = date_time.weekday()
        available_date = datetime.datetime.now()
        available_date =str(available_date.strftime("%Y-%m-%d"))
    else:
        available_date = datetime.datetime.strptime(available_date,"%Y-%m-%d")
        day = available_date.weekday()
        available_date = str(available_date.strftime("%Y-%m-%d"))
    day = weekdays[day]
    query = {"day": day, "doctor_id": ObjectId(session['doctor_id'])}
    time_slots = time_slots_collection.find(query)
    return render_template("view_doctor_slots.html", available_date=available_date, doctor=doctor, slot=slot, time_slots=time_slots)

def formate_time(time):
    date = datetime.datetime.strptime(str(datetime.datetime.now().date())+" "+time,"%Y-%m-%d %H:%M")
    time = str(date.strftime("%I"))+":"+str(date.strftime("%M"))+" "+str(date.strftime("%p"))
    return time

def formate_time2(time):
    date = datetime.datetime.strptime(str(datetime.datetime.now().date())+" "+time,"%Y-%m-%d %H:%M")
    time = str(date.strftime("%I"))+":"+str(date.strftime("%M"))+" "+str(date.strftime("%p"))
    return time

app.run(debug=True)
