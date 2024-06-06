from flask import Flask, request, jsonify 
import psycopg2
import asyncpg

app = Flask(__name__)

conn = psycopg2.connect("dbname=lab6alina user=alina3 password=1111", client_encoding="utf8")
cursor = conn.cursor()

@app.route('/convert', methods=['GET'])
def convert_currency():
    currency_name = request.args.get('currency_name')
    amount = float(request.args.get('amount'))
    
    cursor.execute("SELECT rate FROM currencies WHERE currency_name = %s", (currency_name,))
    currency_data = cursor.fetchone()
    
    if not currency_data:
        return jsonify({'message': 'Валюта,не найденная в базе данных'}), 404
    
    rate = float(currency_data[0])
    converted_amount = rate * amount
    
    return jsonify({'converted_amount': converted_amount}), 200

@app.route('/currencies', methods=["GET"])
def get_currencies():
    cursor.execute('SELECT * FROM currencies')
    currencies = cursor.fetchall()
    
    currencies_list = [{'currency_name': row[1], 'rate': row[2]} for row in currencies]
    
    return jsonify({'currencies': currencies_list}), 200

@app.route('/currency_exists', methods=['GET'])
def currency_exists():
    currency_name = request.args.get('currency_name')
    
    cursor.execute('SELECT EXISTS(SELECT 1 FROM currencies WHERE currency_name = %s)', (currency_name,))
    result = cursor.fetchone()

    return jsonify({'exists': result[0]})


if __name__ == '__main__':
    app.run(port=5002)
