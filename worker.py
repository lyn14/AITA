import redis
import json

def get_data_from_task():
    REDIS_CONN_PARAMS = {
        "host" : "127.0.0.1",
        "password" : "123456" ,
        "port" : '6379' ,
        "encoding" : 'utf-8'
    }
    conn = redis.Redis (**REDIS_CONN_PARAMS)
    data = conn.brpop ("task_queue" , timeout=100)
    # task_queue的形状：{ "task_queue" :[ ... , { "task_id_2": index_2, "number_1": num } , { "task_id_1": index_1 , "number_2": num }  ] }
    return json.loads(data[1].decode('utf-8'))

def run():
    while 1:
        task_dict = get_data_from_task()
        if not task_dict:
            continue
        

if __name__ == "__main__":
    run()
