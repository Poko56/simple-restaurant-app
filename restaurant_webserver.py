#!/usr/bin/env python
# -*- coding: utf-8 -*-

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

# CRUDのためのライブラリをインポート
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# セッションの起動とデータベースとの接続
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
# SQLAlchemyでCRUDの操作を行うためにセッションを使用
DBSession = sessionmaker(bind=engine)
session = DBSession()

# クライアントからサーバーに送られたHTTPリクエストに応じて処理を変更
class webserverHandler(BaseHTTPRequestHandler):
    # GETリクエスト
    def do_GET(self):
        try:
            # レストラン一覧メニュー
            if self.path.endswith("/restaurants/"):
                # 全てのレストラン一覧ページをDBより取得
                restaurants = session.query(Restaurant).all()

                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ''
                output += '<html><head>'
                output += '<style>li {margin-bottom: 25px;}</style>'
                output += '</head><body>'
                output += '<h1>Simple Restaurant Menu</h1>'

                output += '<a href="restaurants/new/">Register new restaurants</a>'
                output += '<br>'
                output += '<ul>'
                for restaurant in restaurants:
                    output += '<li>{name} - id: {id}<br><a href="{id}/edit/">Edit</a>\
                                <a href="{id}/delete/">Delete</a></li>'.format(name=restaurant.name, id=restaurant.id)
                output += '</ul>'
                output += '</body></html>'

                self.wfile.write(output)
                return

            # レストランの新規登録ページを表示
            if self.path.endswith("/new/"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ''
                output += '<html><body>'
                output += '<h1>Register a new Restaurant</h1>'

                output += '<form method="POST" enctype="multipart/form-data" action="/restaurants/new/">'
                output += '<label>Restaurant Name</label>'
                output += '<input required name="newRestaurantName" type="text">'
                output += '<input type="submit" value="Sublit">'
                output += '</form>'

                output += '</body></html>'
                self.wfile.write(output)
                return

            # レストランの編集ページを表示
            if self.path.endswith("/edit/"):
                restaurantIDPath = self.path.split('/')[2]
                # 指定したIDからレストランを取得
                myRestaurantQuery = session.query(Restaurant).filter_by(id=restaurantIDPath).one()

                # 指定したIDに対応するレストランが存在する場合には、ステータスコード200を送信
                if myRestaurantQuery:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()

                    output = ''
                    output += '<html><body>'
                    output += '<h1>You are now editing {name} - Id: {id}</h1>'.format(name=myRestaurantQuery.name, id=myRestaurantQuery.id)

                    output += '<form method="POST" enctype="multipart/form-data" action="/restaurants/{id}/edit/".>'.format(id=myRestaurantQuery.id)
                    output += '<label>Restaurant Name'
                    output += '<input required name="newRestaurantName" type="text" value="{name}"></label><br>'.format(name=myRestaurantQuery.name)
                    output += '<input type="submit" value="Rename">'
                    output += '</form>'

                    self.wfile.write(output)
                    return

            # 削除ページを表示
            if self.path.endswith("/delete/"):
                restaurantIDPath = self.path.split('/')[2]
                myRestaurantQuery = session.query(Restaurant).filter_by(id=restaurantIDPath).one()

                if myRestaurantQuery:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()

                    output = ''
                    output += '<html><body>'
                    output += '<h1>Are you sure to delte {name} - Id: {id}?</h1>'.format(name=myRestaurantQuery.name, id=myRestaurantQuery.id)

                    output += '<form method="POST" enctype="multipart/form-data" action="/restaurants/{id}/delete/".>'.format(id=myRestaurantQuery.id)
                    output += '<input type="submit" value="Delete">'
                    output += '</form>'

                    self.wfile.write(output)
                    return

        except IOError:
            self.send_error(404, "File not found %s" % self.path)


    # POSTリクエスト
    def do_POST(self):
        try:
            # レストランを削除
            if self.path.endswith("/delete/"):
                restaurantIDPath = self.path.split("/")[2]
                myRestaurantQuery = session.query(Restaurant).filter_by(
                    id=restaurantIDPath).one()
                # 指定したIDのレストランが存在する場合にレストランを削除して一覧ページに301リダイレクト
                if myRestaurantQuery:
                    session.delete(myRestaurantQuery)
                    # 変更を確定
                    session.commit()
                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    # 一覧ページにリダイレクト
                    self.send_header('Location', '/restaurants/')
                    self.end_headers()

            # レストランを編集
            if self.path.endswith("/edit/"):
                # cgi.parse_headerで取得したformの値をctype, pdictに格納
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newRestaurantName')
                    restaurantIDPath = self.path.split("/")[2]

                    myRestaurantQuery = session.query(Restaurant).filter_by(
                        id=restaurantIDPath).one()
                    # 指定したIDのレストランが存在する場合には
                    # 変更を確定してレストラン一覧ページに301リダイレクト
                    if myRestaurantQuery != []:
                        myRestaurantQuery.name = messagecontent[0]
                        session.add(myRestaurantQuery)
                        session.commit()
                        self.send_response(301)
                        self.send_header('Content-type', 'text/html')
                        # 一覧ページにリダイレクト
                        self.send_header('Location', '/restaurants/')
                        self.end_headers()


            # レストランを新規登録
            if self.path.endswith("restaurants/new/"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newRestaurantName')

                    newRestaurant = Restaurant(name=messagecontent[0])
                    session.add(newRestaurant)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    # 一覧ページにリダイレクト
                    self.send_header('Location', '/restaurants/')
                    self.end_headers()


            self.wfile.write(output)

        except:
            pass


def main():
    try:
        # 開放するポート番号を指定
        port = 8080
        server = HTTPServer(('', port), webserverHandler)
        print("Web server running on port %s" % port)
        print("Open http://localhost:8080/restaurants/")
        server.serve_forever()

    except KeyboardInterrupt:
        print("\n^C entered, stopping web server...")
        server.socket.close()


if __name__ == '__main__':
    main()
