# app.py
from flask import Flask

# Flask 객체 인스턴스 생성
app = Flask(__name__)

@app.route('/cs/api/v1/OCPP/authorize/999332') # 접속하는 url
def ev():
    return {"hello":"ev"}

if __name__=="__main__":
    app.run(debug=True, threaded=True)
    # host 등을 직접 지정하고 싶다면
    # app.run(host="127.0.0.1", port="5000", debug=True)
