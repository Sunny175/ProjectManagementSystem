import re
import uuid
import datetime as dt
import firebase_admin
import pyrebase
from firebase_admin import credentials, auth, storage
from datetime import datetime
from firebase_admin import credentials, auth
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_mail import Mail, Message
import mailtrap as mt

app = Flask(__name__)
app.secret_key = "session"
app.config['UPLOAD'] = "static/uploads/"

app.config['MAIL_SERVER']='smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'sunnykadia2183@gmail.com'
app.config['MAIL_PASSWORD'] = 'rkoijnajcvwhreqa'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

config = {
    "apiKey": "AIzaSyD7w1t1naoWypN4eEZUhiZhq0l0G6xMdvk",
    "authDomain": "projectmanagement-3e8a8.firebaseapp.com",
    "databaseURL": "https://projectmanagement-3e8a8-default-rtdb.firebaseio.com",
    "projectId": "projectmanagement-3e8a8",
    "storageBucket": "projectmanagement-3e8a8.appspot.com",
    "messagingSenderId": "398063613086",
    "appId": "1:398063613086:web:05aa2a5bb0ccb2d821778f",
    "measurementId": "G-DBHEPCK3YT"
}

firebase = pyrebase.initialize_app(config=config)
authentication = firebase.auth()
database = firebase.database()
cred = credentials.Certificate('firebase_private_key.json')
app_storage = firebase_admin.initialize_app(cred, {
    'storageBucket': 'projectmanagement-3e8a8.appspot.com',
}, name='storage')
firebase_admin.initialize_app(cred)


# Login
@app.route("/", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        try:
            user = authentication.sign_in_with_email_and_password(email, password)
            if user is not None:
                if not firebase_admin._apps:
                    firebase_admin.initialize_app(cred)
                user_id = firebase_admin.auth.get_user_by_email(email)
                session['user_id'] = user_id.uid
                session["user_email"] = email
                admin_user = database.child("Admin").get()
                admin_user_email = admin_user.val()

                if email == admin_user_email['Sunny']['email']:
                    session['user_name'] = admin_user_email['Sunny']['fname']
                    return redirect(url_for("admin", name=session.get('user_name')))
                else:
                    return redirect(url_for('employeeDashboard'))
            else:
                flash("Please check  credentials!!!")
        except Exception as e:
            flash(e)
    return render_template("login.html")


@app.route("/employee/dashboard", methods=["post", "get"])
def employeeDashboard():
    tasks = database.child("Tasks").get()
    emp_tasks = []
    employee = database.child("Employee").get()

    for emp in employee.each():
        if emp.val()['email'] == session.get("user_email"):
            session['user_name'] = emp.val()['name']

    for task in tasks.each():
        if session.get("user_name") == task.val()['assigned_to']:
            emp_tasks.append(task)

    return render_template("emp_dashboard.html", emp_tasks=emp_tasks)


@app.route("/employee/dashboard/todo/<id>")
def todo(id):
    tasks = database.child("Tasks").get()
    status = "To Do"
    for task in tasks.each():
        if id == task.val()['id']:
            key = task.key()
    database.child("Tasks").child(key).update({"status": status})
    return redirect(url_for("employeeDashboard"))


@app.route("/employee/dashboard/inprogress/<id>")
def inprogress(id):
    print("In Progress")
    tasks = database.child("Tasks").get()
    status = "In Progress"
    for task in tasks.each():
        if id == task.val()['id']:
            key = task.key()
    database.child("Tasks").child(key).update({"status": status})
    return redirect(url_for("employeeDashboard"))


@app.route("/employee/dashboard/done/<id>")
def done(id):
    print("Done")
    tasks = database.child("Tasks").get()
    status = "Done"
    for task in tasks.each():
        if id == task.val()['id']:
            key = task.key()
    database.child("Tasks").child(key).update({"status": status})
    return redirect(url_for("employeeDashboard"))


@app.route("/employee/details")
def employeeDetails():
    employee = database.child("Employee").get()
    for emp in employee.each():
        if session.get("user_email") == emp.val()['email']:
            user = emp
            session['assigned_pc'] = emp.val()['assigned_pc']
    return render_template("emp_details.html", user=user)


@app.route("/employee/settings", methods=["get", "post"])
def employeeSettings():
    updatePassword()
    return render_template("emp_settings.html")


@app.route("/employee/history")
def employeeHistory():
    return render_template("emp_history.html")


@app.route("/employee/history/screen-shots", methods=["GET", 'POST'])
def employeeScreenShot():
    if request.method == "POST":
        startdate = request.form.get('date')
        data = screenShotHistory(startdate, session.get("assigned_pc"))
        return render_template("emp_screen_shot.html", date=startdate, data=data)
    return render_template("emp_screen_shot.html")


@app.route("/admin")
def admin():
    employees = database.child("Employee").get()
    total_employee = len(employees.val())
    admin_user = database.child("Admin").get().val()
    return render_template("admin.html", name=admin_user['Sunny']['fname'], total_employee=total_employee)


@app.route("/admin/details")
def details():
    admin_user = database.child("Admin").get().val()
    fname = admin_user['Sunny']['fname']
    mname = admin_user['Sunny']['mname']
    lname = admin_user['Sunny']['lname']
    position = admin_user['Sunny']['position']
    email = admin_user['Sunny']['email']
    gender = admin_user['Sunny']['gender']
    phone = admin_user['Sunny']['phone']
    dob = admin_user['Sunny']['dob']
    quote = admin_user['Sunny']['quote']
    return render_template("details.html", fname=fname, mname=mname, lname=lname, position=position, email=email,
                           gender=gender, phone=phone, dob=dob, quote=quote)


@app.route("/admin/employee", methods=['get', 'post'])
def employee():
    if request.method == 'POST' and request.form.get('editForm'):
        name = request.form.get("name")
        position = request.form.get("position")
        id = request.form.get("id")
        phone = request.form.get("phone")
        email = request.form.get("email")
        department = request.form.get("department")
        doj = request.form.get("doj")
        assigned_pc = request.form.get("assigned_pc")
        result = database.child("Employee").get()
        for res in result.each():
            if id == res.val()['id']:
                key = res.key()
        database.child("Employee").child(key).update({
            "name": name,
            "position": position,
            "phone": phone,
            "email": email,
            "department": department,
            "doj": doj,
            "assigned_pc": assigned_pc
        })
        flash("Data update successfully.")
    employee = database.child('Employee').get()
    return render_template('employee.html', employee=employee)


@app.route("/admin/employee/add", methods=["POST", "GET"])
def addEmployee():
    if request.method == "POST":
        name = request.form.get("name")
        position = request.form.get("position")
        id = request.form.get("id")
        phone = request.form.get("phone")
        email = request.form.get("email")
        department = request.form.get("department")
        doj = request.form.get("doj")
        assigned_pc = request.form.get("assigned_pc")
        file = request.files["profile_pic"]
        # file.save(os.path.join(app.config['UPLOAD'], file.filename))
        # print(file.filename)
        # storage.child("employee_images").put(file)
        data = {
            "name": name,
            "position": position,
            "id": id,
            "phone": phone,
            "email": email,
            "department": department,
            "doj": doj,
            "assigned_pc": assigned_pc
        }
        database.child("Employee").push(data)
        # os.remove(temp.name)
        msg = Message('Hello from the Secure Infotech!', sender='sunnykadia2183@gmail.com', recipients=[email])
        msg.body = f"hey, Your email address and password for website is email: {email} and password: 123456"
        mail.send(msg)
        authentication.create_user_with_email_and_password(email, password=123456)
        redirect(url_for("employee"))
    return redirect(url_for("employee"))


@app.route("/admin/employee/remove/<id>")
def removeData(id):
    data = database.child("Employee").get()
    for record in data.each():
        if record.val()['id'] == id:
            database.child("Employee").child(record.key()).remove()
            flash("Data deleted successfully.")
            return redirect(url_for("employee"))
    return None


@app.route("/admin/settings", methods=['get', 'post'])
def setting():
    updatePassword()
    return render_template("settings.html")

def updatePassword():
    if request.method == "POST":
        current_password = request.form.get("currentpassword")
        password = request.form.get("password")
        repeat_password = request.form.get("repeatpassword")
        if current_password == repeat_password:
            flash("Please enter different password.")
        elif password == repeat_password:
            firebase_admin.auth.update_user(uid=session.get('user_id'), password=password)
            flash("Password updated successfully")

@app.route("/admin/project-management", methods=['post', 'get'])
def projectManagement():
    projects = database.child("Tasks").get()
    employees = database.child("Employee").get()
    if request.method == "POST":
        task_name = request.form.get("name")
        task_assigned_to = request.form.get("employee")
        task_due_date = request.form.get("due_date")
        task_desc = request.form.get("desc")
        task_status = request.form.get("status")
        task_id = "T" + str(uuid.uuid1())
        data = {
            "name": task_name,
            "id": task_id,
            "assigned_to": task_assigned_to,
            "due_date": task_due_date,
            "description": task_desc,
            "status": task_status
        }
        database.child("Tasks").push(data)
        flash("Data is Successfully added.")
        return redirect(url_for("projectManagement"))
    return render_template("project_management.html", projects=projects, employees=employees)


@app.route("/admin/project-management/edit", methods=["post", "get"])
def editProjectData():
    if request.method == "POST":
        task_name = request.form.get('task_name')
        task_id = request.form.get('task_id')
        task_assigned_to = request.form.get('assigned_to')
        task_due_date = request.form.get('due_date')
        task_desc = request.form.get('desc')
        task_status = request.form.get('status')
        tasks = database.child("Tasks").get()
        data = {
            "name": task_name,
            "id": task_id,
            "assigned_to": task_assigned_to,
            "due_date": task_due_date,
            "description": task_desc,
            "status": task_status
        }
        for task in tasks.each():
            if task.val()['id'] == task_id:
                key = task.key()
        database.child("Tasks").child(key).update(data)
        return redirect(url_for("projectManagement"))
    return redirect(url_for("projectManagement"))


@app.route("/admin/project-management/delete/<id>")
def deleteTask(id):
    result = database.child("Tasks").get()
    for res in result.each():
        if res.val()['id'] == id:
            database.child("Tasks").child(res.key()).remove()
            flash("Data deleted successfully")
            return redirect(url_for("projectManagement"))
    return redirect(url_for("projectManagement"))


@app.route("/admin/history")
def history():
    return render_template("history.html")


@app.route("/admin/history/active-time", methods=["post", "get"])
def activeTime():
    if request.method == "POST":
        date = request.form.get("date")
        employee = database.child("Employee").get()
        return render_template("activetime.html", date=date, employee=employee)
    return render_template("activetime.html")


@app.route("/admin/history/active-time/screen-shots/<name>/<assigned_pc>/<date>")
def screenShot(name, assigned_pc, date):
    data = screenShotHistory(date, assigned_pc)
    return render_template("screenshot.html", name=name, data=data)


def screenShotHistory(date, assigned_pc):
    bucket = storage.bucket(app=app_storage)
    blobs = bucket.list_blobs(prefix=assigned_pc)
    img_url = []
    dates = []
    times = []
    current_imgs = []
    pattern = r'/(\d+\.\d+)\.'
    for blob in blobs:
        img_url.append(blob.generate_signed_url(dt.timedelta(seconds=10000), method='GET'))
    for img in img_url:
        list = re.findall(pattern, img)
        img_date = float(list[0])
        dateTime = datetime.fromtimestamp(img_date)
        img_date = dateTime.date()
        time = dateTime.time()
        if str(img_date) == date:
            dates.append(img_date)
            times.append(time)
            current_imgs.append(img)
    return zip(current_imgs, times)


@app.route("/forget-password", methods=["POST", "GET"])
def forget_password():
    if request.method == "POST":
        cred = credentials.Certificate('firebase_private_key.json')
        firebase_admin.initialize_app(cred, name="forget")
        email = request.form.get("email")
        user = firebase_admin.auth.get_user_by_email(email)
        if user.uid is not None:
            session['user_id'] = user.uid
            return redirect(url_for("reset_password", user_id=user.uid))
        else:
            flash("User does not exist!!!")
    return render_template("forget_password.html")


@app.route("/reset-password/<user_id>", methods=["post", "get"])
def reset_password(user_id):
    if request.method == "POST":
        if request.form.get("password") == request.form.get("cpassword"):
            password = request.form.get("password")
            firebase_admin.auth.update_user(uid=user_id, password=password)
            return render_template("login.html")
        elif request.form.get("password") is None and request.form.get("cpassword") is None:
            flash("Enter the some value in fields.")
        else:
            flash("Both value should be same.")
    return render_template("reset_password.html", user_id=user_id)


@app.route("/")
def logout():
    session.clear()
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
