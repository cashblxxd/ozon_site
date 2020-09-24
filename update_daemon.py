import pymongo
from pprint import pprint
import secrets
from mongo_queue.queue import Queue
import time
import datetime
import dateutil.relativedelta
from ozon_api import get_postings_list, get_posting_info, get_items_ids, get_item_info, print_acts, get_item_state_rev,\
     get_labels, get_new_postings_list, get_posting_status_update
import random
import string
from mongo import mark_done, get_files_list, get_file, save_file
import requests
import multiprocessing
import traceback
from collections import OrderedDict


def load_new_postings(apikey, client_id, data, client):
    if data["last_updated"] is None:
        neww = get_new_postings_list(apikey, client_id, (datetime.datetime.now() + dateutil.relativedelta.relativedelta(months=-1)).replace(day=1))
    else:
        neww = get_new_postings_list(apikey, client_id, data["last_updated"] + dateutil.relativedelta.relativedelta(days=-1))
    data["last_updated"] = datetime.datetime.now()
    for i in neww:
        k = get_posting_info(i, apikey, client_id)
        client.ozon_data.postings_pool.update_one({
            "posting_number": i["posting_number"]
        }, {"$set": k}, upsert=True)


def load_new_postings_job(apikey, client_id, client):
    data = client.ozon_data.postings_ids.find_one({
        "creds": f"{apikey}:{client_id}"
    })
    if data is None:
        data = {
            "creds": f"{apikey}:{client_id}",
            "last_updated": None
        }
    load_new_postings(apikey, client_id, data, client)
    if "_id" in data:
        print(1)
        client.ozon_data.postings_ids.update_one({
            "_id": data["_id"]
        }, {"$set": data})
        print("done 1")
    else:
        print(2)
        client.ozon_data.postings_ids.insert_one(data)
        print("done 2")


def update_postings_status(apikey, client_id, timedelta, client):
    '''
    pprint({
        "creds": f"{apikey}:{client_id}",
        "date": {
            "$gte": datetime.datetime.now() + {
                "2h": dateutil.relativedelta.relativedelta(hours=-2),
                "6h": dateutil.relativedelta.relativedelta(hours=-6),
                "2d": dateutil.relativedelta.relativedelta(days=-2),
                "1w": dateutil.relativedelta.relativedelta(weeks=-1),
                "2w": dateutil.relativedelta.relativedelta(weeks=-2),
                "1m": dateutil.relativedelta.relativedelta(months=-1),
                "2m": dateutil.relativedelta.relativedelta(months=-2),
            }[timedelta]
        },
        "status": {
            "$ne": "delivered"
        }
    })
    '''
    data = client.ozon_data.postings_pool.find({
        "creds": f"{apikey}:{client_id}",
        "status": {
            "$ne": "delivered"
        }
    })
    print(data.count())
    new_data = []
    for i in data:
        if i["status"] != "delivered":
            print("updating ...", i["posting_number"])
            k = get_posting_status_update(apikey, client_id, i["posting_number"])
            if i["posting_number"] == "32532022-0046-1":
                print(k)
            i["status"] = k
            new_data.append(i)
    for i in new_data:
        client.ozon_data.postings_pool.update_one({
            "posting_number": i["posting_number"]
        }, {"$set": i}, upsert=True)


def update_postings(api_key, client_id, timedelta, client):
    print('got it')
    update_postings_status(api_key, client_id, timedelta, client)
    print('loaded new')
    load_new_postings_job(api_key, client_id, client)
    print("updated, done")


'''
def update_postings(apikey, client_id, client, timedelta="1d"):
    data = client.ozon_data.postings_ids.find_one({
        "creds": f"{apikey}:{client_id}"
    })
    if data is None:
        data = {
            "creds": f"{apikey}:{client_id}",
            "last_updated": None,
        }
            # last_updated = ((datetime.datetime.now() + dateutil.relativedelta.relativedelta(months=-1)).replace(day=1))
            # last_updated = data["last_updated"] + dateutil.relativedelta.relativedelta(hours=-2)
    was_not_empty = data["order_ids"]["all"]
    data = load_new_postings(apikey, client_id, data, client)
    if "_id" in data:
        print(1)
        client.ozon_data.postings_ids.update_one({
            "_id": data["_id"]
        }, {"$set": data})
        print("done 1")
    else:
        print(2)
        client.ozon_data.postings_ids.insert_one(data)
        print("done 2")
    if was_not_empty:
        update_postings_status(apikey, client_id, timedelta, client)
'''


def load_new_items(apikey, client_id, client):
    for i in ["VISIBLE", "INVISIBLE", "EMPTY_STOCK", "READY_TO_SUPPLY", "STATE_FAILED"]:
        for j in get_items_ids(apikey, client_id, i):
            k = get_item_info(j["product_id"], j["offer_id"], apikey, client_id)
            k["status"] = i
            client.ozon_data.items_pool.update_one({
                "id": f'{j["product_id"]}:{j["offer_id"]}'
            }, {"$set": k}, upsert=True)


'''
def update_items(api_key, client_id, client):
    data = client.ozon_data.items.find_one({
        "creds": f"{api_key}:{client_id}"
    })
    if data is None:
        data = {
            "creds": f"{api_key}:{client_id}",
            "data": OrderedDict(),
            "ids": {
                "all": [],
                "processing": [],
                "moderating": [],
                "processed": [],
                "failed_moderation": [],
                "failed_validation": [],
                "failed": []
            }
        }
    #pprint(data)
    print("the data current")
    neww = get_items_ids(api_key, client_id)
    #pprint(neww)
    print("got", len(neww))
    items_add = OrderedDict()
    ids_add = {
        "all": [],
        "processing": [],
        "moderating": [],
        "processed": [],
        "failed_moderation": [],
        "failed_validation": [],
        "failed": []
    }
    for i in neww:
        print("...", f'{i["product_id"]}:{i["offer_id"]}')
        x_id = f'{i["product_id"]}:{i["offer_id"]}'
        k = get_item_info(i["product_id"], i["offer_id"], api_key, client_id)
        data["data"][x_id] = k
        ids_add[get_item_state_rev(k["Статус"])].append(x_id)
    for i in data["ids"]:
        data["ids"][i] = ids_add[i] + data["ids"][i]
    print("collected", len(data["data"]))
    if "_id" in data:
        client.ozon_data.items.update_one({
            "_id": data["_id"]
        }, {"$set": data})
    else:
        client.ozon_data.items.insert_one(data)
    print("updated!")
'''


def deliver_postings(api_key, client_id, postings_numbers, client):
    postings = []
    print(postings_numbers)
    for i in postings_numbers:
        data = client.ozon_data.postings_pool.find_one({
            "posting_number": i
        })
        if data is None:
            continue
        headers = {
            'Client-Id': str(client_id),
            'Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            "packages": [{"items": data["metadata"]["products"]}],
            "posting_number": i
        }
        r = requests.post(url="http://api-seller.ozon.ru/v2/posting/fbs/ship", headers=headers, json=payload).json()
        pprint(r)
        if "result" in r:
            print("inserting...")
            postings.append(i)
            data["status"] = "awaiting_deliver"
        client.ozon_data.postings_pool.update_one({
            "_id": data["_id"]
        }, {"$set": data})
    return True,

'''
def get_test():
    flist = get_files_list("68349970-1c11-412a-a3f6-19ac61b94210", "33345")
    content = get_file(flist[list(flist.keys())[2]]["file_id"])
    with open("file.pdf", "wb") as f:
        f.write(content)
'''


def upload_act_file(api_key, client_id, client):
    name, content = print_acts(api_key, client_id)
    save_file(api_key, client_id, name, content, client)


def upload_labels(api_key, client_id, posting_numbers, client):
    name, content = get_labels(api_key, client_id, posting_numbers)
    save_file(api_key, client_id, name, content, client)


def work(channel="postings_priority"):
    """
    :param
    channel: ["items_priority", "items_queue", "postings_priority", "postings_queue", "act_queue", "labels_queue", "deliver_queue"]
    :return: None
    """
    client = pymongo.MongoClient("mongodb+srv://dbUser:qwep-]123p=]@cluster0-ifgr4.mongodb.net/Cluster0?retryWrites=true&w=majority", maxPoolSize=None)
    queue = Queue(client.update_queue_db.update_queue, consumer_id=''.join(random.choice(string.ascii_lowercase) for i in range(10)), timeout=300, max_attempts=3)
    while True:
        for channel in ["items_priority", "items_queue", "postings_priority", "postings_queue", "act_queue", "labels_queue", "deliver_queue"]:
            k = queue.next(channel=channel)
            if k:
                #print(k.job_id)
                job_data = k.payload
                #print("look ma i got a job")
                pprint(job_data)
                try:
                    if channel.startswith("postings"):
                        update_postings(job_data["api_key"], job_data["client_id"], "1m", client)
                    elif channel.startswith("items"):
                        #print("gotta update items")
                        load_new_items(job_data["api_key"], job_data["client_id"], client)
                    elif channel.startswith("act"):
                        upload_act_file(job_data["api_key"], job_data["client_id"], client)
                    elif channel.startswith("labels"):
                        upload_labels(job_data["api_key"], job_data["client_id"], job_data["posting_numbers"], client)
                    elif channel.startswith("deliver"):
                        deliver_postings(job_data["api_key"], job_data["client_id"], job_data["posting_numbers"], client)
                    mark_done(job_data["job_id"], client)
                    k.complete()
                except:
                    traceback.print_exc()
                    k.release()


if __name__ == "__main__":
    for channel in ["items_priority", "items_queue", "postings_priority", "postings_queue", "act_queue", "labels_queue", "deliver_queue"]:
        d = multiprocessing.Process(name=secrets.token_urlsafe(), target=work, args=(channel,))
        d.start()
        d.join()
