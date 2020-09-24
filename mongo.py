import pymongo
from pprint import pprint
import secrets
from mongo_queue.queue import Queue
import string
import random
import gridfs
import datetime
from bson.objectid import ObjectId


def user_exist(email, password, client):
    data = client.userdata.users.find_one({
        "email": email,
        "password": password
    })
    pprint(data)
    if data is None:
        return False, {}
    return True, {
        "email": data["email"],
        "accounts_token": data["accounts_token"]
    }


def user_create(email, password, client):
    accounts_token = secrets.token_urlsafe()
    client.userdata.users.insert_one({
        "email": email,
        "password": password,
        "accounts_token": accounts_token
    })
    client.userdata.accounts.insert_one({
        "token": accounts_token,
        "order": [],
        "data": {}
    })
    return True, {
        "email": email,
        "accounts_token": accounts_token
    }


def change_password(email, old_password, new_password, client):
    client.userdata.users.update_one({
        "email": email,
        "password": old_password
    }, {"$set": {
        "password": new_password
    }})


def reset_password(email, new_password, client):
    client.userdata.users.update_one({
        "email": email
    }, {"$set": {
        "password": new_password
    }})


def email_taken(email, client):
    return not (client.userdata.users.find_one({
        'email': email,
    }) is None)


def put_confirmation_token(email, password, client):
    confirmation_token = secrets.token_urlsafe()
    client.userdata.confirmation_tokens.insert_one({
        "token": confirmation_token,
        "email": email,
        "password": password
    })
    return confirmation_token


def get_confirmation_token(token, client):
    data = client.userdata.confirmation_tokens.find_one({
        "token": token
    })
    if data is None:
        return False, "Not found"
    email, password = data["email"], data["password"]
    client.userdata.confirmation_tokens.delete_one(data)
    return True, (email, password)


def put_reset_token(email, client):
    reset_token = secrets.token_urlsafe()
    client.userdata.confirmation_tokens.insert_one({
        "token": reset_token,
        "email": email
    })
    return reset_token


def get_reset_token(token, client):
    data = client.userdata.confirmation_tokens.find_one({
        "token": token
    })
    if data is None:
        return False, "Not found"
    email = data["email"]
    client.userdata.confirmation_tokens.delete_one(data)
    return True, email


def clear_queue(client):
    client.update_queue_db.update_queue.delete_many({})
    client.update_queue_db.job_ids.delete_many({})
    client.update_queue_db.sessions_active.delete_many({})


def get_accounts_order_data(accounts_token, client):
    data = client.userdata.accounts.find_one({
        "token": accounts_token
    })
    if data is None:
        return []
    return data["order"], data["data"]


'''
def clear(client):
    client = pymongo.MongoClient("mongodb+srv://dbUser:qwep-]123p=]@cluster0-ifgr4.mongodb.net/Cluster0?retryWrites=true&w=majority")
    client.ozon_data.items_pool.delete_many({})


clear(0)
'''
#clear_queue()


def account_exist_name_apikey_client_id(name, apikey, client_id, token, client):
    data = client.userdata.accounts.find_one({
        "token": token
    })
    if data is None:
        return False, "Not found"
    if name in data["order"]:
        return False, "name"
    for i in data["data"]:
        if apikey == data["data"][i]["apikey"]:
            return False, "apikey"
        elif client_id == data["data"][i]["client_id"]:
            return False, "client_id"
    return True, ""


def add_account(name, apikey, client_id, token, client):
    data = client.userdata.accounts.find_one({
        "token": token
    })
    if data is None:
        return False, "Not found"
    data["order"].append(name)
    data["data"][name] = {
        "apikey": apikey,
        "client_id": client_id
    }
    client.userdata.accounts.update_one({
        "token": token
    }, {"$set": data})


def delete_account_from_db(token, pos, client):
    accounts = client.userdata.accounts.find_one({
        "token": token
    })
    if accounts is None:
        return False, "Not found"
    acc_name = accounts["order"][pos]
    accounts["order"].pop(pos)
    accounts["data"].pop(acc_name)
    client.userdata.accounts.update_one({
        "token": token
    }, {"$set": accounts})
    return True, ""


def init_session(uid, email, accounts_token, client):
    delete_session(uid, client)
    accounts = client.userdata.accounts.find_one({
        "token": accounts_token
    })
    if not accounts:
        client.userdata.accounts.insert_one({
            "token": accounts_token,
            "order": [],
            "data": {}
        })
        accounts = {
            "order": [],
            "data": {}
        }
    client.sessions_data.sessions_active.insert_one({
        "uid": uid,
        "email_show": email.split("@")[0],
        "email": email,
        "accounts_token": accounts_token,
        "cur_pos": 0,
        "panel": "dashboard",
        "tab": "postings_all",
        "done": ""
    })


def get_session(uid, client):
    return client.sessions_data.sessions_active.find_one({
        "uid": uid
    })


def modify_session(uid, data, client):
    client.sessions_data.sessions_active.update_one({
        "uid": uid
    }, {"$set": data})


def delete_session(uid, client):
    client.sessions_data.sessions_active.delete_one({
        "uid": uid
    })


def mark_pending(job_id, client):
    client.update_queue_db.job_ids.insert_one({
        "job_id": job_id
    })
    print("inserted")


def mark_done(job_id, client):
    client.update_queue_db.job_ids.delete_one({
        "job_id": job_id
    })


def check_job(job_id, client):
    return client.update_queue_db.job_ids.find_one({
        "job_id": job_id
    }) is None


def get_items(api_key, client_id, client, type="items_all"):
    q = {
        "creds": f"{api_key}:{client_id}"
    }
    if type != "items_all":
        q["status"] = type.upper()
    return client.ozon_data.items_pool.find(q).sort('date', -1)


def get_postings(api_key, client_id, client, type="postings_all"):
    q = {
        "creds": f"{api_key}:{client_id}"
    }
    if type != "postings_all":
        q["status"] = type
    return client.ozon_data.postings_pool.find(q).sort('date', -1)


def save_file(api_key, client_id, name, content, client):
    fs = gridfs.GridFS(client.files)
    file_id = fs.put(content, filename=name)
    client.user_files_list.user_files_list.insert_one({
        "creds": f"{api_key}:{client_id}",
        "file_id": file_id,
        "date": datetime.datetime.now(),
        "name": name
    })


def get_files_list(api_key, client_id, client):
    return client.user_files_list.user_files_list.find({
        "creds": f"{api_key}:{client_id}"
    }).sort("date", -1)


def get_file(f_id, client):
    data = client.files.fs.chunks.find_one({
        "files_id": ObjectId(f_id)
    })
    if data is None:
        return None
    return data["data"]


def delete_file(api_key, client_id, f_id, client):
    data = client.user_files_list.user_files_list.find_one({
        "creds": f"{api_key}:{client_id}",
        "file_id": ObjectId(f_id)
    })
    if data is None:
        return
    delete_file_gridfs(f_id, client)
    client.user_files_list.user_files_list.delete_one(data)


def delete_file_gridfs(f_id, client):
    client.files.fs.chunks.delete_one({
        "file_id": ObjectId(f_id)
    })


def check_job_not_exist(api_key, client_id, channel, client): # , type=None):
    q = {
        "api_key": api_key,
        "client_id": client_id,
        "channel": channel
    }
    """
    if type:
        q["type"] = type
    """

    data = client.update_queue_db.update_queue.find_one(q)
    return data is None or data["attempts"] > 1


def insert_deliver_job(api_key, client_id, posting_numbers, job_id, client):
    if check_job_not_exist(api_key, client_id, "deliver_queue", client):
        queue = Queue(client.update_queue_db.update_queue, consumer_id=''.join(random.choice(string.ascii_lowercase) for i in range(10)), timeout=300, max_attempts=3)
        queue.put({"api_key": api_key, "client_id": client_id, "posting_numbers": posting_numbers,  "job_id": job_id}, channel="deliver_queue")
        mark_pending(job_id, client)


def insert_items_update_job(api_key, client_id, job_id, client):
    if check_job_not_exist(api_key, client_id, "items_priority", client):
        queue = Queue(client.update_queue_db.update_queue, consumer_id=''.join(random.choice(string.ascii_lowercase) for i in range(10)), timeout=300, max_attempts=3)
        queue.put({"api_key": api_key, "client_id": client_id, "job_id": job_id}, channel="items_priority")
        mark_pending(job_id, client)


def insert_items_regular_update(api_key, client_id, job_id, client):
    if check_job_not_exist(api_key, client_id, "items_priority", client) and check_job_not_exist(api_key, client_id, "items_queue", client):
        queue = Queue(client.update_queue_db.update_queue, consumer_id=''.join(random.choice(string.ascii_lowercase) for i in range(10)), timeout=300, max_attempts=3)
        queue.put({"api_key": api_key, "client_id": client_id, "job_id": job_id}, channel="items_queue")
        mark_pending(job_id, client)


def insert_postings_new_update_job(api_key, client_id, job_id, client):
    if check_job_not_exist(api_key, client_id, "postings_priority", client):
        queue = Queue(client.update_queue_db.update_queue, consumer_id=''.join(random.choice(string.ascii_lowercase) for i in range(10)), timeout=300, max_attempts=3)
        queue.put({"api_key": api_key, "client_id": client_id, "job_id": job_id, "type": "new"}, channel="postings_priority")
        mark_pending(job_id, client)


def insert_postings_status_update_job(api_key, client_id, job_id, client):
    if check_job_not_exist(api_key, client_id, "postings_priority", client):
        queue = Queue(client.update_queue_db.update_queue, consumer_id=''.join(random.choice(string.ascii_lowercase) for i in range(10)), timeout=300, max_attempts=3)
        queue.put({"api_key": api_key, "client_id": client_id, "job_id": job_id, "type": "status"}, channel="postings_priority")
        mark_pending(job_id, client)


def insert_postings_update_job(api_key, client_id, job_id, client):
    if check_job_not_exist(api_key, client_id, "postings_priority", client):
        queue = Queue(client.update_queue_db.update_queue, consumer_id=''.join(random.choice(string.ascii_lowercase) for i in range(10)), timeout=300, max_attempts=3)
        queue.put({"api_key": api_key, "client_id": client_id, "job_id": job_id, "type": "all"}, channel="postings_priority")
        print("put")
        pprint({"api_key": api_key, "client_id": client_id, "job_id": job_id})
        mark_pending(job_id, client)
        print("INSERTED")


def insert_postings_regular_update(api_key, client_id, job_id, client):
    if check_job_not_exist(api_key, client_id, "postings_priority", client) and check_job_not_exist(api_key, client_id, "postings_queue", client):
        queue = Queue(client.update_queue_db.update_queue, consumer_id=''.join(random.choice(string.ascii_lowercase) for i in range(10)), timeout=300, max_attempts=3)
        queue.put({"api_key": api_key, "client_id": client_id, "job_id": job_id}, channel="postings_queue")
        mark_pending(job_id, client)


def insert_act_job(api_key, client_id, job_id, client):
    if check_job_not_exist(api_key, client_id, "act_queue", client):
        queue = Queue(client.update_queue_db.update_queue, consumer_id=''.join(random.choice(string.ascii_lowercase) for i in range(10)), timeout=300, max_attempts=3)
        queue.put({"api_key": api_key, "client_id": client_id, "job_id": job_id}, channel="act_queue")
        mark_pending(job_id, client)


def insert_labels_upload_job(api_key, client_id, posting_numbers, job_id, client):
    data = client.update_queue_db.update_queue.find_one({
        "api_key": api_key,
        "client_id": client_id,
        "posting_numbers": posting_numbers,
        "channel": "labels_queue"
    })
    if data is None or data["attempts"] > 1:
        queue = Queue(client.update_queue_db.update_queue, consumer_id=''.join(random.choice(string.ascii_lowercase) for i in range(10)), timeout=300, max_attempts=3)
        queue.put({"api_key": api_key, "client_id": client_id, "job_id": job_id, "posting_numbers": posting_numbers}, channel="labels_queue")
        mark_pending(job_id, client)
