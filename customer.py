from flask import Flask, Response, request,flash, render_template, make_response, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
from datetime import datetime
import math
import requests

from smartystreets_python_sdk import StaticCredentials, exceptions, ClientBuilder
from smartystreets_python_sdk.us_street import Lookup


app=Flask(__name__)
CORS(app)

app.config['SECRET_KEY']='zy112612' # 密码
app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://admin:zy112612@e6156-1.cudpmdtzmg9e.us-east-1.rds.amazonaws.com:3306/customer'
    # 协议：mysql+pymysql
    # 用户名：root
    # 密码：2333
    # IP地址：localhost
    # 端口：3306
    # 数据库名：runoob #这里的数据库需要提前建好
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']=True
db=SQLAlchemy(app)

#{ "email": "wg@gmail.com","password": "0002"}
@app.before_request
def check_login():
    if request.path == '/customer/login':
        data = json.loads(request.get_data())
        password = data['password']
        email = data['email']
        
        try:
            sql = "SELECT * FROM Customers where email = '{}' ".format(email)
            result = db.session.execute(sql).fetchone()
        except Exception as err:
            return {"state": False, "message": "error! input error"}
        if result:
            stored_password= result[2]
            if stored_password != password:
                
                print("unmatch")
                return {"state": False,"message":"password unmatch"}
               
        else:
            return {"state": False, "message": "please register"}
        

@app.before_request
def run():
    if request.path == '/customer/register':
        auth_id = "c832f79c-cc29-3a15-c118-51733a6b5929"
        auth_token = "CoGbY7DbR8qNdUPu3aZh"
        data = json.loads(request.get_data())
        address = data['address']
        zipcode= data["zipcode"]
       

        credentials = StaticCredentials(auth_id, auth_token)

        client = ClientBuilder(credentials).build_us_street_api_client()
       
        lookup = Lookup()
        
        lookup.street = address
        lookup.zipcode = zipcode
        

        try:
            client.send_lookup(lookup)
        except exceptions.SmartyException as err:
            print(err)
            return {"message": "input error", "state": False}

        result = lookup.result

        if not result:
            print("No candidates. This means the address is not valid.")
            return {"message": "invalid address", "state": False}
    
@app.after_request
def af3(response):
    if request.path == '/customer/register':
    # print(request.environ.get('SERVER_PROTOCOL'))
    # print(len((response.data.decode('utf-8').split(":"))))
    # print(json.loads(response.get_data())["state"])
    # if response.data.decode('utf-8').split(":")[2][1] == 't':
        if json.loads(response.get_data())["state"] :
            data=json.loads(request.get_data())
            print(data)
            username = data['username']
            email= data["email"]
            # print(username)
            sellers_check = requests.post("https://00xi30tpb2.execute-api.us-east-1.amazonaws.com/test/helloworld", data=json.dumps({"username":username,  "email": email}))

    return response
 
@app.route('/', methods=['GET'])
def home():
    return 'Hello World!'



    
    



#{"username":"ywang", "password":"0002", "email": "wg@gmail.com", "address": "400w"}
@app.route('/customer/register', methods=['GET', 'POST'])
def register():
    response = ""
    if request.method == 'POST':
        data = json.loads(request.get_data())

        username = data['username']
        password = data['password']
        email = data['email']
        address = data['address']
        print(email)
        try:
            sql = "SELECT COUNT('{}') FROM Customers where email = '{}' ".format(email, email)
            result = db.session.execute(sql).fetchall()[0][0]
        except Exception as err:
            return {"state": False, "message": "error! input error"}
        
        print(result)
        if result > 0:
            response = {"state": False,"message": "error! email is used"}
        else:
            try:
                sql= "INSERT INTO Customers VALUES ('{}', '{}', '{}', '{}');".format(email,username, password, address)
                db.session.execute(sql)
            except Exception as err:
                return {"state": False,"message": "error! input error"}
            sql = 'select * from Customers'
            result = db.session.execute(sql)
            print(result.fetchall())
            
            response = {"state": True,"message": "register successfully"}
       
    return response

#{email: string, username:string}
#{state: True/False message: string, explain whether login is successful or not,}

@app.route('/customer/googleLogin', methods=['GET', 'POST'])
def google_login():
    
    if request.method == 'POST':
        data = json.loads(request.get_data())
        username = data['username']
        email = data['email']
        
        try:
            sql = "SELECT * FROM Customers where email = '{}' ".format(email)
            result = db.session.execute(sql).fetchone()
        except Exception as err:
            return {"state": False, "message": "error! input error"}
        
        if result :
            print("successfully")
            response= {"state": True, "message":"login successfully"}
            
        else:
            try:
                sql= "INSERT INTO Customers VALUES ('{}', '{}', null, null);".format(email,username)
                db.session.execute(sql)
            except Exception as err:
                return {"state": False,"message": "error! input error"}

            response= {"state": True, "message": "register and login successfully"}
        
    return response


@app.route('/customer/login',methods=['GET','POST'])
def login(): 
    data = json.loads(request.get_data())
    
    email = data['email']
    try:
        sql = "SELECT * FROM Customers where email = '{}' ".format(email)
        result = db.session.execute(sql).fetchone()
    except Exception as err:
            return {"state": False, "message": "error! input error"}
    print("successfully")
    username= result[1]
    address= result[3]

    return {"state": True, "message":"login successfully", "username": username, "address": address}

@app.route('/customer/modifyPassword', methods=['GET', 'POST'])
def customer_modify_password():
    if request.method == 'POST':
        data = json.loads(request.get_data())
        email = data['email']
        oldpwd = data['currPw']
        newpwd = data['modifiedPw']

        try:
            sql = "SELECT * FROM Customers where Email = '{}' AND Pwd = '{}'".format(email, oldpwd)
            result = db.session.execute(sql).fetchone()
        except Exception as err:
            return {"message": "error! change password error","state":False}

        if result :
            stored_password= result[2]
            print(stored_password)
            try: 
                sql = "UPDATE Customers SET Pwd = '{}' where Email = '{}'".format(newpwd, email)
                db.session.execute(sql)
            except Exception as err:
                return {"message": "error! change password error","state":False}
            try:
                sql = 'select * from Customers'
                result = db.session.execute(sql)
                print(result.fetchall())
            except Exception as err:
                return {"state":False,"message": "error! change password error"}
            msg = {"message":"password modified successfully","state":True}
        else:
            msg = {"state":False,"message":"old password unmatch"}

        return msg

#{"address":"aaaa", "email": "wang@gmail.com", "username":"yifan"}
@app.route('/customer/modifyInfo', methods=['GET', 'POST'])
def customer_modify_information():
    if request.method == 'POST':
        data = json.loads(request.get_data())
        email = data['email']
        username = data['username']
        address = data['address']
        
        try: 
            sql = "UPDATE Customers SET Name = '{}', address = '{}'  where Email = '{}'".format(username, address, email)
            db.session.execute(sql)
        except Exception as err:
            return {"message": "error! change information error","state":False}
        
        try:
            sql = 'select * from Customers'
            result = db.session.execute(sql)
        except Exception as err:
            return {"message": "error! change information error","state":False}
        
        msg = {"state":True,"message":"information modified successfully"}

        return msg



# {"email": "wg@gmail.com"}
@app.route("/customer/history/<page>", methods=['POST'])
def get_customer_history(page):
    page=int(page)-1
    pages=5
    if request.method == 'POST':
        data = json.loads(request.get_data())
        email = data['email']
        sql = "SELECT o.OID, o.Time FROM Places p, Orders o WHERE p.Email = '{}' AND p.OID = o.OID".format(email)
        result = db.session.execute(sql).fetchall()
        print(result)
        print(len(result))
        max_page=math.ceil(len(result)/pages)
        print(max_page)
        if page < max_page:
            try:
                sql = "SELECT o.OID, o.Time FROM Places p, Orders o WHERE p.Email = '{}' AND p.OID = o.OID LIMIT {} OFFSET {} ".format(email, pages, page*5)
                result2 = db.session.execute(sql).fetchall()
            except Exception as err:
                return {"state": False, "message": "error! input error"}
            json_list=[]
            for row in result2:
                json_list.append([x for x in row])  
            return {"max_page": max_page, "history": json_list}
        else: 
            return {"state": False, "message": "error! do not have data"}
        



#{email: string, timestamp: time,( current time), order:dictionary{merchandise id: amount}}
# { "email":"wg@gmail.com", "timestamp":"2022-12-11 17:30:00" }
@app.route("/customer/place_order", methods=['POST'])
def customer_place_order():
    response={}
    if request.method == 'POST':
        data = json.loads(request.get_data())
        email = data['email']
        time= data['timestamp']
        try: 
            sql='SELECT Max(oid) FROM Orders'
            max_oid = db.session.execute(sql).fetchone()
        except Exception as err:
            return {"message": "error! change information error","state":False}
        oid=max_oid[0]+1
        print(oid)
        try:
            sql="INSERT INTO Orders VALUES ('{}', '{}')".format(oid,time)
            db.session.execute(sql)
        except Exception as err:
            print("order")
            return {"message": "error! change information error","state":False}

        try:
            sql="INSERT INTO Places VALUES ('{}', '{}')".format(email, oid)
            db.session.execute(sql)
        except Exception as err:
            print("places")
            return {"message": "error! change information error","state":False}

        response["message"]= True
        response['state']= True
        response['oid']= oid

    return response

@app.route("/people/<email>", methods=["GET"])
def get_customer_by_email(email):
    
    sql = "select * from Customers where email = '" + email + "'"
    result = db.session.execute(sql).fetchone()

    if result:
        data_email=result[0]
        name=result[1]
        password= result[2]
        address= result[3]
        list=[data_email, name, password, address]
        
        rsp = Response(json.dumps(list), status=200, content_type="application/json")
        
    else:
        rsp = Response("NOT FOUND", status=404, content_type="text/plain")

    return rsp
    

if __name__=='__main__':

    app.run(host='0.0.0.0', port=8080, debug=True)