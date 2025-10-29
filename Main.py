from flask import Flask, render_template, request, redirect, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch', methods=['GET'])
def fetch():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL tidak diberikan"}), 400

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code == 200:
            return redirect(url)
        else:
            return jsonify({"error": f"Gagal akses URL, status {r.status_code}"}), r.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
