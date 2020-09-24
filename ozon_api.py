import requests
from pprint import pprint
import time
from datetime import datetime
import dateutil.relativedelta
from PyPDF2 import PdfFileMerger
import os


def get_items_ids(shop_api_key, client_id, state):
    print("Getting ids...")
    cur = 1
    r = {"total": 1}
    result = []
    while r["total"] != 0:
        headers = {
            'Client-Id': str(client_id),
            'Api-Key': shop_api_key,
            'Content-Type': 'application/json'
        }
        payload = "{\n  \"filter\": {\n    \"visibility\": \"" + state + "\"\n  },\n  \"page\": " + str(cur) + ",\n  \"page_size\": 1000\n}"
        r = requests.post(url="http://api-seller.ozon.ru/v1/product/list", headers=headers, data=payload).json()["result"]
        result.extend(r["items"])
        cur += 1
    return result


def get_product_parameters(product_id, offer_id, shop_api_key, client_id):
    headers = {
        'Client-Id': str(client_id),
        'Api-Key': shop_api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        "filter": {
            "offer_id": offer_id,
            "product_id": product_id
        }
    }
    return requests.post(url="http://api-seller.ozon.ru/v2/products/info/attributes", headers=headers, json=payload).json()


def get_sku(r):
    fbo, fbs = "", ""
    for i in r.get("sources", []):
        if i["source"] == "fbo":
            fbo = i["sku"]
        elif i["source"] == "fbs":
            fbs = i["sku"]
    return {
        "fbo": fbo,
        "fbs": fbs
    }


def get_item_state(state):
    if state == "":
        return ""
    if state == "processing":
        return "Информация о товаре добавляется в систему, ожидайте"
    if state == "moderating":
        return "Товар проходит модерацию, ожидайте"
    if state == "processed":
        return "Информация обновлена"
    if state == "failed_moderation":
        return "Товар не прошел модерацию"
    if state == "failed_validation":
        return "Товар не прошел валидацию"
    if state == "failed":
        return "Возникла неизвестная ошибка"


def get_item_state_rev(state):
    if state == "":
        return ""
    if state == "Информация о товаре добавляется в систему, ожидайте":
        return "processing"
    if state == "Товар проходит модерацию, ожидайте":
        return "moderating"
    if state == "Информация обновлена":
        return "processed"
    if state == "Товар не прошел модерацию":
        return "failed_moderation"
    if state == "Товар не прошел валидацию":
        return "failed_validation"
    if state == "Возникла неизвестная ошибка":
        return "failed"


def parse_date_short(s):
    if not s:
        return "-"
    date = datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
    return date.strftime('%d-%m-%Y %H:%M:%S')


def parse_date_long(s):
    if not s: return ""
    date = datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')
    return date.strftime('%H:%M:%S %d-%m-%Y')


def get_item_info(product_id, offer_id, shop_api_key, client_id):
    headers = {
        'Client-Id': str(client_id),
        'Api-Key': shop_api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        "offer_id": offer_id,
        "product_id": product_id
    }
    r = requests.post(url="http://api-seller.ozon.ru/v2/product/info", headers=headers, json=payload).json()["result"]
    """
        Артикул 
Баркод 
Наименование 
Статус 
видимость на сайте 
Доступно на складе 
Текущая цена
'''
        "Ozon Product ID": product_id,
        "FBO OZON SKU ID": sku_ids["fbo"],
        "FBS OZON SKU ID": sku_ids["fbs"],
        
        
        
        
        "Дата создания": parse_date_long(r.get("created_at", "")),
        
        
        "Цена до скидки (перечеркнутая цена), руб.": str(r.get("old_price", "")).replace(".", ","),
        "Цена Premium, руб.": str(r.get("premium_price", "")).replace(".", ","),
        "Рыночная цена, руб.": str(r.get("recommended_price", "")).replace(".", ","),
        "Размер НДС, %": {"": "0", "0.000000": "0", "0.100000": "10%", "0.200000": "20%", }[str(r.get("vat", "0"))]'''
    """
    result = {
        "offer_id": offer_id,
        "images": r["images"],
        "name": r["name"],
        "visibility": "Показывается" if r.get("visible", 0) else "Не показывается",
        "fbs_stock": r.get("stocks", {}).get("present", "0"),
        "price": r.get("marketing_price", "-"),
        "price_actual": "-",
        "creds": f"{shop_api_key}:{client_id}",
        "product_id": product_id,
        "date": r.get("created_at", datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
    }
    try:
        price = float(result["price"])
        price -= max(0.15 * price, 150)
        price -= 75
        result["price_actual"] = str(price)
    except Exception:
        pass
    return result


def get_new_postings_list(apikey, client_id, since=None):
    print("since.......................", since)
    headers = {
        'Client-Id': str(client_id),
        'Api-Key': apikey,
        'Content-Type': 'application/json'
    }
    payload = {
        "dir": "desc",
        "filter": {},
        "limit": 50,
        "offset": 0,
        "with": {
            "barcodes": False
        }
    }
    if not (since is None):
        payload["filter"]["since"] = since.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"
    pprint(payload)
    r = requests.post(url="http://api-seller.ozon.ru/v2/posting/fbs/list", headers=headers, json=payload).json()
    pprint(r)
    r = r["result"]
    postings = []
    while r:
        postings.extend(r)
        payload["offset"] += 50
        r = requests.post(url="http://api-seller.ozon.ru/v2/posting/fbs/list", headers=headers, json=payload).json()["result"]
    return postings



def get_postings_list(shop_api_key, client_id, status=None, since=(datetime.now() + dateutil.relativedelta.relativedelta(months=-1)).replace(day=1)):
    headers = {
        'Client-Id': str(client_id),
        'Api-Key': shop_api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        "dir": "desc",
        "filter": {
            "since": since.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z",
            "to": (datetime.now()).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"
        },
        "limit": 50,
        "offset": 0,
        "with": {
            "barcodes": False
        }
    }
    if status and status != "ALL":
        payload["filter"]["status"] = status
    postings = []
    r = requests.post(url="http://api-seller.ozon.ru/v2/posting/fbs/list", headers=headers, json=payload).json()
    pprint(r)
    r = r["result"]
    while r:
        postings.extend(r)
        payload["offset"] += 50
        r = requests.post(url="http://api-seller.ozon.ru/v2/posting/fbs/list", headers=headers, json=payload).json()["result"]
    return postings


def get_posting_status(s):
    if s == "": return ""
    if s == "awaiting_packaging": return "Ожидает упаковки"
    if s == "not_accepted": return "Не принят в сортировочном центре"
    if s == "arbitration": return "Ожидает решения спора"
    if s == "awaiting_deliver": return "Ожидает отгрузки"
    if s == "delivering": return "Доставляется"
    if s == "driver_pickup": return "У водителя"
    if s == "delivered": return "Доставлено"
    if s == "cancelled": return "Отменено"


def get_sum(price_str, q_str):
    if not (price_str and q_str): return ""
    return str(float(price_str) * float(q_str))


def get_details(products):
    return '\n'.join(f'{product.get("quantity", "-")} шт. Артикул: {product.get("offer_id", "-")} {product.get("name", "-")}' for product in products)


def get_product_image(sku, shop_api_key, client_id):
    try:
        headers = {
            'Client-Id': str(client_id),
            'Api-Key': shop_api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            "sku": sku,
        }
        r = requests.post(url="http://api-seller.ozon.ru/v2/product/info", headers=headers, json=payload).json()["result"]
        return r["images"][0]
    except Exception as e:
        return "https://image.flaticon.com/icons/png/512/1602/1602620.png"


def get_posting_status_update(apikey, client_id, posting_number):  # posting_number
    headers = {
        'Client-Id': str(client_id),
        'Api-Key': apikey,
        'Content-Type': 'application/json'
    }
    payload = {
        "posting_number": posting_number,
    }
    return requests.post(url="http://api-seller.ozon.ru/v2/posting/fbs/get", headers=headers, json=payload).json()["result"]["status"]


def get_prices_sum(products):
    summ = 0
    for product in products:
        s = product.get("price", "-")
        if s != '-':
            summ += float(s)
    return str(summ)


def get_posting_info(r, shop_api_key, client_id):
    products = r.get("products", [{}])
    result = {
        "creds": f"{shop_api_key}:{client_id}",
        "date": r.get("in_process_at", "-"),
        "shipment_date": r.get("shipment_date", "-"),
        "order_number": r.get("order_number", "-"),
        "posting_number": r.get("posting_number", "-"),
        "details": get_details(products),
        "images": [get_product_image(products[i].get("sku", "-"), shop_api_key, client_id)
                     for i in range(len(products))],
        "price": get_prices_sum(products),
        "status": r["status"],
        "metadata": {
            "products": [{
                "quantity": i["quantity"],
                "sku": i["sku"],
            } for i in products],
        }
    }
    return result


'''# Стоимость !!!!!!!!!!!!!!!!!!
        "Дата отгрузки": parse_date_short(r.get("shipment_date", "-")),
        
        '''

# datetime.strptime(i["Принят в обработку"], '%d-%m-%Y %H:%M:%S') >= ((datetime.now() + dateutil.relativedelta.relativedelta(months=-1)).replace(day=1)) and i["Номер отправления"] in actual_posting_numbers


def print_acts(shop_api_key, client_id):
    headers = {
        'Client-Id': str(client_id),
        'Api-Key': shop_api_key,
        'Content-Type': 'application/json'
    }
    pprint(headers)
    print("http://api-seller.ozon.ru/v2/posting/fbs/act/create")
    r = requests.post(url="http://api-seller.ozon.ru/v2/posting/fbs/act/create", headers=headers, json={}).json()
    pprint(r)
    try:
        res_id = r["result"]["id"]
    except Exception as e:
        print(e)
        return (False,)
    ready = False
    for i in range(100):
        headers = {
            'Client-Id': str(client_id),
            'Api-Key': shop_api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            "id": res_id
        }
        r = requests.post(url="http://api-seller.ozon.ru/v2/posting/fbs/act/check-status",
                          headers=headers, json=payload).json()["result"]["status"]
        if r == "error":
            return (False,)
        if r == "ready":
            ready = True
            break
        time.sleep(2)
    if ready:
        headers = {
            'Client-Id': str(client_id),
            'Api-Key': shop_api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            "id": res_id
        }
        r = requests.post(url="http://api-seller.ozon.ru/v2/posting/fbs/act/get-pdf", headers=headers, json=payload)
        return f"Акт {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}", r.content


def get_labels(api_key, client_id, posting_numbers):
    print("getting:", posting_numbers)
    filenames = []
    for i in range(len(posting_numbers)):
        headers = {
            'Client-Id': str(client_id),
            'Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            "posting_number": [posting_numbers[i]],
        }
        r = requests.post(url="http://api-seller.ozon.ru/v2/posting/fbs/package-label", headers=headers, json=payload)
        try:
            s = r.json()
            if s["error"]["code"] == "POSTINGS_NOT_READY":
                print("fuck i failed")
                print(s["error"]["message"])
                continue
        except Exception:
            pass
        filename = str(client_id) + "_" + str(i) + ".pdf"
        filenames.append(filename)
        with open(filename, 'wb') as f:
            f.write(r.content)
    merger = PdfFileMerger()
    for pdf in filenames:
        merger.append(pdf)
    name = f"Маркировки {datetime.now().strftime('%H:%M:%S %d-%m-%Y')}"
    with open(name, "w+") as f:
        f.write("")
    merger.write(name)
    merger.close()
    for file in filenames:
        os.remove(file)
    with open(name, "rb") as f:
        content = f.read()
    os.remove(name)
    return name, content


#print(get_posting_status_update("68349970-1c11-412a-a3f6-19ac61b94210", "33345", "32532022-0046-1"))