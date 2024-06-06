from flask import Flask, request, jsonify 
import psycopg2
import asyncpg
app = Flask(__name__)

conn = psycopg2.connect("dbname=lab6alina user=alina3 password=1111", client_encoding="utf8")
cursor = conn.cursor()

@app.route('/load', methods=['POST'])
def load_currency():
    data = request.get_json()
    currency_name = data.get('currency_name')
    rate = data.get('rate')
    
    cursor.execute('SELECT * FROM currencies WHERE currency_name = %s', (currency_name,))
    existing_currency = cursor.fetchone()
    
    if existing_currency:
        return jsonify({'message': 'Валюта уже сущетсвует в базе данных'}), 400
    
    cursor.execute('INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)', (currency_name, rate)) 
    conn.commit()
    
    return jsonify({'message': 'Валюта добавлена'}), 200

@app.route('/update_currency', methods=['POST'])
def update_currency():
    data = request.get_json()
    currency_name = data.get('currency_name')
    new_rate = data.get('rate')
    
    cursor.execute('SELECT * FROM currencies WHERE currency_name = %s', (currency_name,))
    existing_currency = cursor.fetchone()
    
    if not existing_currency: 
        return jsonify({'message': 'Валюта не сущетсвует в базе данных'}), 404
        
    cursor.execute('UPDATE currencies SET rate = %s WHERE currency_name = %s', (new_rate, currency_name)) 
    conn.commit()
    
    return jsonify({'message': 'Валюта успешно обновлена'}), 200

@app.route('/delete', methods=['POST'])
def delete_currency():
    data = request.get_json()
    currency_name = data.get('currency_name')
    
    cursor.execute('SELECT * FROM currencies WHERE currency_name = %s', (currency_name,)) 
    existing_currency = cursor.fetchone()
    
    if not existing_currency:
        return jsonify({'message': 'Валюта не существует в базе данных'}), 404
        
    cursor.execute('DELETE FROM currencies WHERE currency_name = %s', (currency_name,)) 
    conn.commit()
    
    return jsonify({'message': 'Валюта успешно удалена'}), 200
if __name__ == '__main__':
    app.run(port=5001)
