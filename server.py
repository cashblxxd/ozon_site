from flask import *
import pymongo
from mongo import user_exist, put_confirmation_token, get_confirmation_token, user_create,\
    get_session, init_session, modify_session, delete_session, get_items, get_postings, \
    insert_items_update_job, insert_act_job, insert_labels_upload_job, insert_deliver_job,\
    get_files_list, get_file, delete_file, email_taken, change_password, account_exist_name_apikey_client_id, add_account, \
    delete_account_from_db, insert_postings_new_update_job, insert_postings_status_update_job,\
    check_job_not_exist, put_reset_token, get_reset_token, reset_password, insert_postings_update_job, get_accounts_order_data
from mailer import send_join_mail, send_reset_mail
from pprint import pprint
from validate_email import validate_email
import secrets
import io


app = Flask(__name__)
app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"
app.secret_key = "OCML3BRawWEUeaxcuKHLpw"
app.jinja_env.cache = {}
mgclient = pymongo.MongoClient("mongodb+srv://dbUser:qwep-]123p=]@cluster0-ifgr4.mongodb.net/Cluster0?retryWrites=true&w=majority")


@app.route('/', methods=['GET', 'POST'])
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """
    :param
    panel: "dashboard", "downloads", "dynamics", "sales", "analytics", "purchases", "losses", "roadmap", "flow",
           "competitiors", "money", "settings"
    tab: "items_all", "visible", "ready_to_supply", "state_failed", "empty_stock", "invisible",
         "postings_all", "awaiting_packaging", "awaiting_deliver", "arbitration", "delivering", "delivered", "cancelled"
    done: "items", "postings_new", "postings_update", "act", "file_deleted", "labels", "deliver", "postings_new_inprogress", "postings_update_inprogress"
    :return:
    """
    if "uid" not in session:
        session["uid"] = secrets.token_urlsafe()
        return redirect("/login")
    mongosession = get_session(session["uid"], mgclient)
    if mongosession is None:
        return redirect("/login")
    action = request.args.get("action", "None")
    changed = False
    accounts, accounts_data = get_accounts_order_data(mongosession["accounts_token"], mgclient)
    ''' elif update == "postings_new":
            pos = request.args.get("pos", "None")
            if pos.isdigit() and int(pos) < len(accounts):
                account = accounts_data[accounts[int(pos)]]
                if not check_job_not_exist(account["apikey"], account["client_id"], "postings_priority", mgclient, type="status"):
                    mongosession["done"] = "postings_update_inprogress"
                else:
                    
                    mongosession["done"] = "postings_new"
                changed = True'''
    if action == "update":
        update = request.args.get("update", "None")
        if update == "items":
            pos = request.args.get("pos", "None")
            if pos.isdigit() and int(pos) < len(accounts):
                account = accounts_data[accounts[int(pos)]]
                insert_items_update_job(account["apikey"], account["client_id"], f'{account["apikey"]}:{account["client_id"]}', mgclient)
                mongosession["done"] = "items"
                changed = True
        elif update == "postings_update":
            pos = request.args.get("pos", "None")
            if pos.isdigit() and int(pos) < len(accounts):
                account = accounts_data[accounts[int(pos)]]
                insert_postings_update_job(account["apikey"], account["client_id"], f'{account["apikey"]}:{account["client_id"]}', mgclient)
                # insert_postings_new_update_job(account["apikey"], account["client_id"], f'{account["apikey"]}:{account["client_id"]}', mgclient)
                mongosession["done"] = "postings_update"
                changed = True
        elif update == "act":
            pos = request.args.get("pos", "None")
            if pos.isdigit() and int(pos) < len(accounts):
                account = accounts_data[accounts[int(pos)]]
                insert_act_job(account["apikey"], account["client_id"], f'{account["apikey"]}:{account["client_id"]}', mgclient)
                mongosession["done"] = "act"
                changed = True
        elif update == "get_label":
            posting_number = request.args.get("posting_number", "None")
            pos = request.args.get("pos", "None")
            if posting_number != "None" and pos.isdigit() and int(pos) < len(accounts):
                account = accounts_data[accounts[int(pos)]]
                insert_labels_upload_job(account["apikey"], account["client_id"], [posting_number], f'labels_queue:{account["apikey"]}:{account["client_id"]}', mgclient)
                mongosession["done"] = "labels"
                changed = True
    elif action == "delete":
        delete = request.args.get("delete", "None")
        if delete == "file":
            file_id = request.args.get("file_id", "None")
            account = accounts_data[accounts[mongosession["cur_pos"]]]
            delete_file(account["apikey"], account["client_id"], file_id, mgclient)
            mongosession["done"] = "file_deleted"
            changed = True
    elif action == "get":
        get = request.args.get("get", "None")
        if get == "file":
            file_id = request.args.get("file_id", "None")
            file_name = request.args.get("file_name", "None")
            return send_file(io.BytesIO(get_file(file_id, mgclient)), attachment_filename=file_name + '.pdf', as_attachment=True, mimetype="application/pdf")
    cur_pos, panel, done, tab = request.args.get("u", "None"), request.args.get("panel", "None"), request.args.get("done", "None"), request.args.get("tab", "None")
    if request.method == 'POST':
        print(1)
        posting_numbers = request.form.getlist('posting_number')
        print(posting_numbers)
        if posting_numbers and len(accounts) > 0:
            if request.form['action'] == 'Печать маркировок':
                account = accounts_data[accounts[mongosession["cur_pos"]]]
                insert_labels_upload_job(account["apikey"], account["client_id"], posting_numbers, f'labels_queue:{account["apikey"]}:{account["client_id"]}', mgclient)
                done = "labels"
            if request.form['action'] == 'Собрать':
                account = accounts_data[accounts[mongosession["cur_pos"]]]
                insert_deliver_job(account["apikey"], account["client_id"], posting_numbers, f'deliver_queue:{account["apikey"]}:{account["client_id"]}', mgclient)
                done = "deliver"
    email_show = mongosession["email_show"]
    email = mongosession["email"]
    if panel != "None" and panel in {"dashboard", "downloads", "dynamics", "sales", "analytics", "purchases", "losses",
                                     "roadmap", "flow", "competitiors", "money", "settings"}:
        mongosession["panel"] = panel
        changed = True
    if cur_pos != "None" and str(cur_pos).isdigit() and int(cur_pos) <= len(accounts):
        mongosession["cur_pos"] = int(cur_pos)
        changed = True
    if tab != "None" and tab in {"items_all", "visible", "ready_to_supply", "state_failed", "empty_stock", "invisible",
                                 "postings_all", "awaiting_packaging", "awaiting_deliver", "arbitration", "delivering",
                                 "delivered", "cancelled"}:
        mongosession["tab"] = tab
        changed = True
    if done != "None" and done in {"items", "postings_new", "postings_update", "act", "file_deleted", "labels", "deliver",
                                   "postings_new_inprogress", "postings_update_inprogress"}:
        mongosession["done"] = done
        changed = True
    if changed:
        if mongosession["panel"] not in {"dashboard", "downloads", "dynamics", "sales", "analytics", "purchases", "losses",
                                         "roadmap", "flow", "competitiors", "money", "settings"}:
            mongosession["panel"] = "dashboard"
        if mongosession["tab"] not in {"items_all", "visible", "ready_to_supply", "state_failed", "empty_stock",
                                       "invisible", "postings_all", "awaiting_packaging", "awaiting_deliver",
                                       "arbitration", "delivering", "delivered", "cancelled"}:
            mongosession["tab"] = "postings_all"
        if mongosession["done"] not in {"items", "postings_new", "postings_update", "act", "file_deleted", "labels", "deliver",
                                        "postings_new_inprogress", "postings_update_inprogress"}:
            mongosession["done"] = ""
        print(mongosession["done"])
        modify_session(session["uid"], mongosession, mgclient)
        return redirect("/dashboard")
    if cur_pos == "None" and "cur_pos" not in mongosession:
        mongosession["cur_pos"] = 0
    if panel == "None" and "panel" not in mongosession:
        mongosession["panel"] = "dashboard"
    if tab == "None" and "tab" not in mongosession:
        mongosession["tab"] = "postings_all"
    if mongosession["panel"] not in {"dashboard", "downloads", "dynamics", "sales", "analytics", "purchases", "losses",
                                     "roadmap", "flow", "competitiors", "money", "settings"}:
        mongosession["panel"] = "dashboard"
    if mongosession["tab"] not in {"items_all", "visible", "ready_to_supply", "state_failed", "empty_stock", "invisible",
                                   "postings_all", "awaiting_packaging", "awaiting_deliver", "arbitration", "delivering",
                                   "delivered", "cancelled"}:
        mongosession["tab"] = "postings_all"
    cur_pos = mongosession["cur_pos"]
    panel = mongosession["panel"]
    tab = mongosession["tab"]
    data = "None"
    d = {}
    if len(accounts) > 0:
        if mongosession["panel"] == "dashboard":
            if mongosession["tab"] in {"items_all", "visible", "ready_to_supply", "state_failed", "empty_stock", "invisible"}:
                account = accounts_data[accounts[cur_pos]]
                data = get_items(account["apikey"], account["client_id"], mgclient, mongosession["tab"])
                if data.count() == 0:
                    data = "None"
                d = {
                    "visible": "В продаже",
                    "ready_to_supply": "Готов к продаже",
                    "state_failed": "С ошибками",
                    "empty_stock": "Снят с продажи",
                    "archive": "В архиве"
                }
            elif mongosession["tab"] in {"postings_all", "awaiting_packaging", "awaiting_deliver", "arbitration",
                                         "delivering", "delivered", "cancelled"}:
                account = accounts_data[accounts[cur_pos]]
                data = get_postings(account["apikey"], account["client_id"], mgclient, mongosession["tab"])
                if data.count() == 0:
                    data = "None"
                d = {
                    "awaiting_packaging": "Ожидает сборки",
                    "awaiting_deliver": "Ожидает отгрузки",
                    "arbitration": "Ожидает решения спора",
                    "delivering": "Доставляется",
                    "delivered": "Доставлен",
                    "cancelled": "Отменён"
                }
        elif mongosession["panel"] == "downloads":
            account = accounts_data[accounts[cur_pos]]
            data = get_files_list(account["apikey"], account["client_id"], mgclient)
    pprint(data)
    if mongosession["done"] in {"items", "postings_new", "postings_update", "act", "file_deleted", "labels", "deliver",
                                "postings_new_inprogress", "postings_update_inprogress"}:
        print(1)
        theme = "success"
        if mongosession["done"] in ["postings_new_inprogress", "postings_update_inprogress"]:
            theme = "warning"
        title = {
            "items": "Список товаров обновляется",
            "postings_new": "Новые заказы загружаются",
            "postings_update": "Список заказов обновляется",
            "act": "Акт формируется, зайдите в Загрузки",
            "file_deleted": "Файл успешно удалён",
            "labels": "Маркировки формируются, зайдите в Загрузки",
            "deliver": "Товары успешно собраны",
            "postings_new_inprogress": "Подождите, пока новые заказы загрузятся",
            "postings_update_inprogress": "Подождите, пока статусы заказов обновятся"
        }[mongosession["done"]]
        mongosession["done"] = ""
        modify_session(session["uid"], mongosession, mgclient)
        print(theme, title)
        return render_template("dashboard.html", email_show=email_show, email=email, data=data, accounts=accounts,
                               cur_pos=cur_pos, panel=panel, tab=tab, done=True, theme=theme, title=title, message="", d=d)
    modify_session(session["uid"], mongosession, mgclient)
    # pprint(mongosession)
    # data: "None", "No any"
    return render_template("dashboard.html", email_show=email_show, email=email, data=data, accounts=accounts,
                           cur_pos=cur_pos, panel=panel, tab=tab, d=d)


@app.route('/help', methods=['GET', 'POST'])
def help():
    return "<h1>Здесь будет FAQ</h1>"


@app.route('/tos', methods=['GET', 'POST'])
def tos():
    return "<h1>Здесь будут правила сервиса</h1>"


@app.route('/mail', methods=['GET', 'POST'])
def mail():
    return "<h1>Здесь будет почта</h1>"


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """
    :param
    action: "done", "delete"
    done: "bad_old_password", "bad_new_password", "passwords_nomatch", "password_success", "name_taken",
          "apikey_taken", "client_id_taken", "account_added", "account_deleted"
    :return:
    """
    if "uid" not in session:
        session["uid"] = secrets.token_urlsafe()
        return redirect("/login")
    mongosession = get_session(session["uid"], mgclient)
    if mongosession is None:
        return redirect("/login")
    if request.method == 'POST':
        action = request.form['action']
        if action == "Сохранить":
            old_password, new_password, password_again = request.form['old_password'], request.form['new_password'], request.form['password_again']
            if not user_exist(mongosession["email"], old_password, mgclient)[0]:
                return redirect("/settings?action=done&done=bad_old_password")
            elif len(new_password) < 8 or new_password.isalpha() or new_password.isdigit() or new_password.isalnum():
                return redirect("/settings?action=done&done=bad_new_password")
            elif new_password != password_again:
                return redirect("/settings?action=done&done=passwords_nomatch")
            else:
                change_password(mongosession["email"], old_password, new_password, mgclient)
                return redirect("/settings?action=done&done=password_success")
        elif action == "Добавить":
            name, apikey, client_id = request.form['name'], request.form['apikey'], request.form['client_id']
            if name and apikey and client_id:
                response, data = account_exist_name_apikey_client_id(name, apikey, client_id, mongosession["accounts_token"], mgclient)
                if response:
                    add_account(name, apikey, client_id, mongosession["accounts_token"], mgclient)
                    return redirect("/settings?action=done&done=account_added")
                elif data == "name":
                    return redirect("/settings?action=done&done=name_taken")
                elif data == "apikey":
                    return redirect("/settings?action=done&done=apikey_taken")
                elif data == "client_id":
                    return redirect("/settings?action=done&done=client_id_taken")
    action = request.args.get("action", "None")
    accounts, accounts_data = get_accounts_order_data(mongosession["accounts_token"], mgclient)
    if action == "done":
        done = request.args.get("done", "None")
        if done in {"bad_old_password", "bad_new_password", "passwords_nomatch", "password_success", "name_taken",
                    "apikey_taken", "client_id_taken", "account_added", "account_deleted"}:
            mongosession["done"] = done
            modify_session(session["uid"], mongosession, mgclient)
            return redirect("/settings")
    elif action == "delete":
        pos = request.args.get("u", "None")
        if pos.isdigit():
            pos = int(pos)
            if pos < len(accounts):
                delete_account_from_db(mongosession["accounts_token"], pos, mgclient)
                return redirect("/settings")
    if mongosession["done"] in {"bad_old_password", "bad_new_password", "passwords_nomatch", "password_success", "name_taken",
                "apikey_taken", "client_id_taken", "account_added", "account_deleted"}:
        theme = {
            "bad_old_password": "error",
            "bad_new_password": "error",
            "passwords_nomatch": "error",
            "password_success": "success",
            "name_taken": "error",
            "apikey_taken": "error",
            "client_id_taken": "error",
            "account_added": "success",
            "account_deleted": "success"
        }[mongosession["done"]]
        title = {
            "bad_old_password": "Неверный старый пароль",
            "bad_new_password": "Новый пароль должен быть не менее 8 символов и содержать буквы, цифры и спецсимволы",
            "passwords_nomatch": "Новый пароль и подтверждение не совпадают",
            "password_success": "Пароль успешно изменён",
            "name_taken": "Магазин с таким именем уже есть",
            "apikey_taken": "Магазин с таким API-Key уже есть",
            "client_id_taken": "Магазин с таким Client ID уже есть",
            "account_added": "Магазин успешно добавлен",
            "account_deleted": "Магазин успешно удалён"
        }[mongosession["done"]]
        mongosession["done"] = ""
        modify_session(session["uid"], mongosession, mgclient)
        return render_template("settings.html", email_show=mongosession["email_show"], email=mongosession["email"], accounts=accounts, account_data=accounts_data, done=True, theme_select=theme, title_select=title)
    return render_template("settings.html", email_show=mongosession["email_show"], email=mongosession["email"], accounts=accounts, account_data=accounts_data)


'''
@app.route('/get_file', methods=['GET', 'POST'])
def posting_labels():
    if "uid" not in session:
        session["uid"] = secrets.token_urlsafe()
        return redirect("/login")
    print(session["uid"])
    mongosession = get_session(session["uid"], mgclient)
    if mongosession is None:
        return redirect("/login")
    q, u = request.args.get("q", "None"), request.args.get("u", "None")
    if q == "None":
        return redirect("/dashboard?panel=downloads")
    if not u.isdigit() or int(u) > len(mongosession["order"]):
        u = mongosession["cur_pos"]
    accounts, accounts_data = get_accounts_order_data(mongosession["accounts_token"], mgclient)
    account = accounts[mongosession["order"][int(u)]]
    flist = get_files_list(account["apikey"], account["client_id"], mgclient)
    if q not in flist:
        return redirect("/dashboard?panel=downloads")
    return send_file(io.BytesIO(get_file(flist[q]["file_id"], mgclient)), attachment_filename=q + '.pdf', as_attachment=True, mimetype="application/pdf")


@app.route('/delete_file', methods=['GET', 'POST'])
def mark_delete():
    if "uid" not in session:
        session["uid"] = secrets.token_urlsafe()
        return redirect("/login")
    print(session["uid"])
    mongosession = get_session(session["uid"], mgclient)
    if mongosession is None:
        return redirect("/login")
    q, u = request.args.get("q", "None"), request.args.get("u", "None")
    if q not in ["items", "postings"]:
        return redirect("/dashboard")
    if not u.isdigit() or int(u) > len(mongosession["order"]):
        u = mongosession["cur_pos"]
    print(q, u)
    accounts, accounts_data = get_accounts_order_data(mongosession["accounts_token"], mgclient)
    account = accounts[mongosession["order"][int(u)]]
    try:
        delete_file(account["apikey"], account["client_id"], q, mgclient)
    except Exception as e:
        print(e)
    return redirect("/dashboard?done=file_deleted")


@app.route('/get_act', methods=['GET', 'POST'])
def get_act():
    if "uid" not in session:
        session["uid"] = secrets.token_urlsafe()
        return redirect("/login")
    print(session["uid"])
    mongosession = get_session(session["uid"], mgclient)
    if mongosession is None:
        return redirect("/login")
    u = request.args.get("u", "None")
    if not u.isdigit() or int(u) > len(mongosession["order"]):
        u = mongosession["cur_pos"]
    accounts, accounts_data = get_accounts_order_data(mongosession["accounts_token"], mgclient)
    account = accounts[mongosession["order"][int(u)]]
    insert_act_job(account["apikey"], account["client_id"], f'get_act:{account["apikey"]}:{account["client_id"]}', mgclient)
    return redirect("/dashboard?done=act")
'''


@app.route('/confirm', methods=['GET', 'POST'])
def confirm_join():
    token = request.args.get("token", "")
    print(token, "token")
    if token:
        response, message = get_confirmation_token(token, mgclient)
        print(response, message)
        if response:
            email, password = message
            response, data = user_create(email, password, mgclient)
            if response:
                return render_template("login.html", email_confirmed=True)
    return redirect("/login")


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if "uid" not in session:
        session["uid"] = secrets.token_urlsafe()
        return redirect("/login")
    mongosession = get_session(session["uid"], mgclient)
    if mongosession is None:
        return redirect("/login")
    delete_session(session.get("uid", "-"), mgclient)
    session.clear()
    return redirect("/login")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, password = request.form.get("email", ""), request.form.get("password", "")
        print(email, password)
        if email and password:
            response, data = user_exist(email, password, mgclient)
            if response:
                email, accounts_token = data["email"], data["accounts_token"]
                if "uid" not in session:
                    session["uid"] = secrets.token_urlsafe()
                mongosession = get_session(session["uid"], mgclient)
                if mongosession is None:
                    init_session(session["uid"], email, accounts_token, mgclient)
                return redirect("/")
            else:
                return render_template("login.html", failed=True)
        return render_template("login.html")
    return render_template("login.html")


@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        email, password, password_again = request.form.get("email", ""), request.form.get("password", ""), request.form.get("password_again", "")
        if email and password:
            print(email, password)
            if email_taken(email, mgclient):
                return render_template("register.html", email_taken=True)
            elif not validate_email(email_address=email, check_regex=True, check_mx=True):
                return render_template("register.html", email_invalid=True)
            elif len(password) < 8 or password.isalpha() or password.isdigit() or password.isalnum():
                return render_template("register.html", password_invalid=True)
            elif password != password_again:
                return render_template("register.html", passwords_nomatch=True)
            else:
                print(1)
                token = put_confirmation_token(email, password, mgclient)
                print(token)
                send_join_mail(email, token)
                return render_template("register.html", registration_success=True)
    return render_template("register.html")


@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email, password, password_again = request.form.get("email", ""), request.form.get("password", ""), request.form.get("password_again", "")
        if password or password_again:
            if len(password) < 8 or password.isalpha() or password.isdigit() or password.isalnum():
                return render_template("reset_password_set.html", password_invalid=True)
            elif password != password_again:
                return render_template("reset_password_set.html", passwords_nomatch=True)
            else:
                reset_password(email, password, mgclient)
                return redirect("/login")
        else:
            token = put_reset_token(email, mgclient)
            send_reset_mail(email, token)
            return render_template("reset_password.html", reset_email_sent=True)
    token = request.args.get("token", "")
    if token:
        response, email = get_reset_token(token, mgclient)
        if response:
            return render_template("reset_password_set.html", email=email)
    return render_template("reset_password.html")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1', threaded=True)

