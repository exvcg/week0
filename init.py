import re
import random
import requests

from bs4 import BeautifulSoup
from pymongo import MongoClient           # pymongo를 임포트 하기(패키지 인스톨 먼저 해야겠죠?)

client = MongoClient('localhost', 27017)  # mongoDB는 27017 포트로 돌아갑니다.
db = client.dbjungle                      # 'dbjungle'라는 이름의 db를 만듭니다.

def insert_user():
    users = [70,15,20]
    for user in users:
        userc = str(user)
        user_data = {"user_id":userc,"password":"0000"}
        db.users.insert_one(user_data)
    
if __name__ == '__main__':
    # 기존의 movies 콜렉션을 삭제하기
    db.users.drop()

    # 영화 사이트를 scraping 해서 db 에 채우기
    insert_user()