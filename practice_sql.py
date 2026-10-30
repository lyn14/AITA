from flask import Flask,request, jsonify
import pymysql
import redis
import uuid , json

# 任务：用户提交和任务内容（一个待处理的1-10中的一个整数），生成任务id（用uuid解决）：
# 若任务内容在redis队列中，或者虽不在redis队列中，但在数据库中，
# 则返回该用户的任务id、任务内容在何处被处理（redis或数据库），以及处理的结果（二进制化这个整数）和状态（success或error）；
# 若任务内容不在redis队列中，也不在数据库中，则返回“任务未完成，请稍后查询结果！”

app = Flask(__name__)

def binary_conversion(n):
    """将整数转换为二进制字符串"""
    return bin(n)[2:]  # 去掉 '0b' 前缀

# 连接MySQL数据库
my_database = pymysql.connect( 
    host='127.0.0.1',
    port=3306,
    user='root',
    password='123456',
    database='new_db',
)
print ("数据库连接成功！")
for i in range (1 , 11):
    num_binary = binary_conversion(i)
    cursor=my_database.cursor()
    cursor.execute ( "INSERT INTO tasks (num_int , num_binary , status , create_time) " \
    "VALUES ( %s , %s , %s ,NOW()) " , (i , num_binary , "success") )
    my_database.commit()
    cursor.close()

print ("数据库初始化完成！")

# query的结构:{ "number": ... }

@app.route("/query_task", methods=["GET"])
def query_task():
    # 1.将任务id作为参数传入，查询redis队列和数据库中是否有该任务的处理结果
    ## 1.1.生成任务id，接收用户提交的任务内容（一个整数1-10）
    index=str(uuid.uuid4())
    num = request.args.get("number")

    ## 1.2.连接redis队列
    redis_connect= {
        "host":"127.0.0.1",
        "port":6379,
        "password":"123456",
        "encoding":"utf-8"
    }
    conn=redis.Redis(**redis_connect)
    
    ## 1.3.将任务id存入redis队列。
    # redis队列的结构：（采用 lpush)
    # { "task_queue" :[ ... , { "task_id_2": index_2, "number_1": num } , { "task_id_1": index_1 , "number_2": num }  ] }
    conn.lpush("task_queue", json.dumps({"task_id": index , "number": num}))
    
    ## 1.4. 生成redis缓存池，以供查阅
    # 使用Redis hash存储任务信息，方便后续查询
    # 结构: num_set : {num_int} -> { num_binary:... , "status": "success" or "error" }
    
    # 计算二进制结果
    for num in range(1, 6):
        try:
            num_int = int(num)
            result = binary_conversion(num_int)
            status = "success"
        except (ValueError, TypeError):
            result = None
            status = "error"
        # 存入Redis缓存池（使用hash结构）
        conn.hset(f"num_set:{num_int}", mapping={
            "num_binary": result,
            "status": status
        })
        # 设置过期时间（可选，例如24小时后自动删除）
        conn.expire(f"num_set:{num_int}", 86400)  # 24小时 = 86400秒
    
        print(f"任务 {num_int} 已存入Redis缓存池")

    """任务1结束
    现在redis池子中有了1-10的整数及其二进制化结果，用户可以通过task_id查询结果。
    """

    # 2.查询任务结果
    ## 2.1 查询redis队列中是否有该任务的处理结果
    
    task_list = conn.lrange("task_queue" , 0 , -1)
    for task in task_list:
        """这块是AI帮我编的，不得不说确实牛逼"""
        task_data = json.loads(task) #task_data = {"task_id": "uuid", "number": "5"}
        if task_data.get("task_id"):
            if task_data.get("task_id") == index:
                num = int (task_data.get("number")) # AI编的代码还是有不严谨的地方
                # 查询Redis缓存池中的结果
                result_data = conn.hgetall(f"num_set:{num}")
                result_status = conn.hget(f"num_set:{num}", "status")
                if result_data and result_status == b"success":
                    return jsonify({
                        "task_id": index,
                        "number": num,
                        "location": "redis",
                        "result": result_data.get(b"num_binary").decode("utf-8"),
                        "status": result_data.get(b"status").decode("utf-8")
                    })
                else:
    ## 2.2 如果redis中没有结果，则查询数据库
                    cursor = my_database.cursor()
                    cursor.execute("SELECT num_binary, status FROM tasks WHERE num_int = %s", (num,))
                    result = cursor.fetchone() #选择下一行
                    if result:
                        return jsonify({
                            "task_id": index,
                            "number": num,
                            "location": "database",
                            "result": result[0],
                            "status": result[1]
                        })
                    else:
                        return jsonify ( {"status": "error", "msg": "任务未完成，请稍后查询结果！"} )
        else:
            return jsonify ( {"status": "error", "msg": "无效任务ID"} )
if __name__ == "__main__":
    app.run(debug=True)

"""总结：该程序实现了任务提交、查询和结果返回的功能，支持在Redis和数据库中查询任务结果。"""