from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        print("Có giao dịch mới!")
        print("Thông tin giao dịch:", data)
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(port=80)
