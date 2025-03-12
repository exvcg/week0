import datetime
from bson import ObjectId
from flask import Flask, make_response, render_template, jsonify, request,redirect,session, url_for
from flask_jwt_extended import *
import requests
from pymongo import MongoClient  # pymongo를 임포트 하기(패키지 인스톨 먼저 해야겠죠?)
from flask.json.provider import JSONProvider
import jwt
import json
import sys
app = Flask(__name__)

client = MongoClient('localhost',27017)  # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbjungle  # 'dbjungle'라는 이름의 db를 만들거나 사용합니다.
app.config["JWT_SECRET_KEY"] = "asedds"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]  # JWT를 쿠키에 저장
app.config["JWT_COOKIE_SECURE"] = False  # HTTPS가 아니어도 허용 (배포 시 True로 변경)
app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"  # 쿠키 이름 설정
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
jwt = JWTManager(app)
#####################################################################################
# 이 부분은 코드를 건드리지 말고 그냥 두세요. 코드를 이해하지 못해도 상관없는 부분입니다.
#
# ObjectId 타입으로 되어있는 _id 필드는 Flask 의 jsonify 호출시 문제가 된다.
# 이를 처리하기 위해서 기본 JsonEncoder 가 아닌 custom encoder 를 사용한다.
# Custom encoder 는 다른 부분은 모두 기본 encoder 에 동작을 위임하고 ObjectId 타입만 직접 처리한다.
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


# 위에 정의되 custom encoder 를 사용하게끔 설정한다.
app.json = CustomJSONProvider(app)

# 여기까지 이해 못해도 그냥 넘어갈 코드입니다.
# #####################################################################################


@app.route('/')
def first():
    return render_template("login_page.html")

@app.route('/login', methods=['POST'])#로그인
def login():
    Uid = request.form['username']
    Password = request.form['Password']
    user = db.users.find_one({"user_id": Uid})
    if (not user) or (user["password"] != Password):  # 평문 비교
        return render_template("login_page.html")

    # JWT 토큰 생성 (1시간 유효)
    access_token = create_access_token(identity=str(user["_id"]), expires_delta=datetime.timedelta(minutes=3))
    response = make_response(redirect(url_for("page",number = 1)))#return의 역할
    response.set_cookie("access_token", access_token, httponly=True)#쿠키 설정
    return response
@app.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect(url_for("first")))
    response.set_cookie("access_token", "", expires=0)  # 쿠키 삭제
    return response
@app.route("/make", methods=['GET'])#게시물 생성
@jwt_required()
def make():
    return render_template("writing_page_mix.html")
@app.route("/listup", methods=['POST'])#게시물 생성
@jwt_required()
def listup():
    title = request.form['title']
    con = request.form['content']
    mcon = request.form['mcontent']
    now = datetime.datetime.now()
    month = now.month 
    day = now.day
    id = get_jwt_identity()
    edu = {'title': title,'md':mcon,'content' : con ,'user': id, 'month': month, 'day' : day }
    result = db.til.insert_one(edu)
    return redirect(url_for("main"))
@app.route("/showup/<id>")#공부내용 가져오기
@jwt_required()
def showup(id):
    current_user = get_jwt_identity()
    userd = db.users.find_one({"_id":ObjectId(current_user)})
    prb = list(db.til.find({"_id":ObjectId(id)}))
    cocom = list(db.ccc.find({'lid':id}))
    rlist = list(db.ccc.find({'user': current_user}))
    dlist = list(db.til.find({'user': current_user}).sort({'month':-1,'day':-1}))
    return render_template("article.html", cont = prb[0], comm = cocom,cvc = current_user,mst = len(dlist), rst = len(rlist),ID = userd["user_id"])
@app.route("/main")
@jwt_required()
def main():
    return redirect(url_for("page",number = 1))
@app.route("/page/<number>")
@jwt_required()
def page(number):
    sets = int(int(number)/10)
    current_user = get_jwt_identity()
    userd = db.users.find_one({"_id":ObjectId(current_user)})
    elist = list(db.til.find().skip(10*(int(number)-1)).limit(10).sort({'month':-1,'day':-1}))
    rlist = list(db.ccc.find({'user': current_user}))
    dlist = list(db.til.find({'user': current_user}).sort({'month':-1,'day':-1}))
    pagenum = int(len(list(db.til.find()))/10) + 1
    return render_template("after_login.html", lessons = elist,ID = userd["user_id"],mst = len(dlist), rst = len(rlist),nums = pagenum,set = sets)    
@app.route("/showlist", methods=['GET'])#게시물리스트 가져오기
@jwt_required()
def showlist():
    current_user = get_jwt_identity()
    asd = list(db.ccc.find)
    elist = list(db.til.find().sort({'month':-1,'day':-1}))
    for ele in elist:
        ele["_id"] = str(ele["_id"])
    userd = db.users.find_one({"_id":ObjectId(current_user)})
    rlist = list(db.ccc.find({'user': current_user}))
    dlist = list(db.til.find({'user': current_user}).sort({'month':-1,'day':-1}))
    return render_template("after_login.html", lessons = elist,ID = userd["user_id"],mst = len(dlist), rst = len(rlist))
@app.route("/showmine/<number>", methods=['GET'])#내 게시물만 가져오기
@jwt_required()
def showmine(number):
    sets = int(int(number)/10)
    current_user = get_jwt_identity()
    pagenum = int(len(list(db.til.find({'user': current_user})))/10) + 1
    userd = db.users.find_one({"_id":ObjectId(current_user)})
    rlist = list(db.ccc.find({'user': current_user}))
    dlist = list(db.til.find({'user': current_user}).sort({'month':-1,'day':-1}))
    return render_template("after_login.html", lessons = dlist,mst = len(dlist), rst = len(rlist),ID = userd["user_id"],nums = pagenum,set = sets)

@app.route("/comment/<lid>", methods=['POST'])#댓글 구현
@jwt_required()
def comment(lid):
    com = request.form["commentx"]
    Uid = get_jwt_identity()
    comments = {'lid': lid , 'content':com , 'user':Uid}
    db.ccc.insert_one(comments)
    rlist = list(db.ccc.find({'user': Uid}))
    dlist = list(db.til.find({'user': Uid}).sort({'month':-1,'day':-1}))
    return redirect(url_for("showup", id = lid))

@app.route("/want/<id>", methods=['GET'])#내용변경요청
@jwt_required()
def want(id):
     con = db.til.find_one({"_id":ObjectId(id)})   
     return render_template("change.html",origin = con)

@app.route("/change/<id>", methods=['POST'])#내용변경수락
@jwt_required()
def change(id):
    title = request.form['title']
    content = request.form["content"]
    mcon = request.form['mcontent']
    result = db.til.update_one({"_id":ObjectId(id)},{'$set': {'title':title ,'content': content,'md':mcon}})
    return redirect(url_for("main"))
@app.route("/cpw")#비번변경창 띄우기
@jwt_required()
def cpw():
    return render_template("password_edit.html")
@app.route("/password", methods=['POST'])#비번변경
@jwt_required()
def password():
    newPass = request.form["password"]
    check = request.form["check"]
    print(newPass)
    print(check)
    if (newPass == check):
        id = get_jwt_identity()
        db.users.update_one({"_id":ObjectId(id)},{'$set': {'password': newPass}})
        return redirect(url_for("logout"))
    
    return redirect(url_for("cpw"))
@app.route("/delete/<id>", methods=['GET'])#삭제
@jwt_required()
def delete(id):
    db.ccc.delete_many({"lid":id})
    result = db.til.delete_one({"_id":ObjectId(id)})
    if result.deleted_count == 1:
        return redirect(url_for("main"))
# @app.route("/like/<id>", methods=['GET'])#좋아요 기능
# @jwt_required()
# def like(id):
#     result = db.til.find_one({"_id":ObjectId(id)})
#     newlike = result['like'] + 1
#     db.til.update_one({"_id":ObjectId(id)},{'$set': {'like': newlike}})
#     return redirect(url_for("main"))
@app.route("/comentmine")#
@jwt_required()
def comentmine():#내가 단 댓글 가져오기
    current_user = get_jwt_identity()
    elist = list(db.ccc.find({'user': current_user}))
    dlist = list(db.til.find({'user': current_user}).sort({'month':-1,'day':-1}))
    return render_template("commentmine.html",coms = elist,mst = len(dlist), rst = len(elist))
@app.route("/cdelete/<id>")
@jwt_required()
def cdelete(id):#내가 단 댓글 가져오기
    lid = db.ccc.find_one({'_id':ObjectId(id)})
    db.ccc.delete_one({'_id':ObjectId(id)})
    return redirect(url_for("showup", id = lid["lid"]))
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return redirect(url_for("first"))

if __name__ == "__main__":
    app.run(debug=True)    