import pymongo
client = pymongo.MongoClient("mongodb+srv://dbUser:qwep-]123p=]@cluster0-ifgr4.mongodb.net/Cluster0?retryWrites=true&w=majority")
client.update_queue_db.update_queue.delete_many({})
client.update_queue_db.job_ids.delete_many({})
# client.sessions_data.sessions_active.delete_many({})

