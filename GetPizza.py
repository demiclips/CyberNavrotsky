from flask import Flask, request, jsonify
import random
import time

app = Flask(__name__)


@app.route('/receive_order', methods=['POST'])
def receive_order():
    data = request.get_json()

    if data:
        name = data.get('name')
        order = data.get('order')
        price = data.get('price')

        print('Name : ' + str(name))
        print('Order Details : ' + str(order))
        print('Total Price   : ' + str(price))

        time.sleep(random.randint(1, 10))

        return jsonify({'status': 'success', 'message': 'Order printed in cmd!'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)