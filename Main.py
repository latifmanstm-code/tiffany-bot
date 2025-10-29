from flask import Flask, request, jsonify, redirect
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <h2>🚀 FB Video Proxy Server</h2>
    <form action="/fetch" method="get">
        <input type="text" name="url" placeholder="Masukkan URL video..." style="width:300px;">
        <button type="submit">Ambil Video</button>
    </form>
    '''

@app.route('/fetch')
def fetch():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL tidak diberikan"}), 400

    try:
        # Proxy request ke URL target
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, stream=True, timeout=10)

        # Redirect langsung ke video
        if response.status_code == 200:
            return redirect(url)
        else:
            return jsonify({"error": f"Gagal mengakses URL. Status: {response.status_code}"}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
