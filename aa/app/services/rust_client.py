import requests

def encrypt_with_rust(data):
    url = "http://127.0.0.1:8080/encrypt"
    try:
        resp = requests.post(url, json={"records": data})
        return resp.json()
    except Exception as e:
        print("⚠️ Rust 암호화 서버가 실행 중이 아닙니다:", e)
        return {"ciphertext": str(data)}
