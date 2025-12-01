import secrets
import base64

def generate_secret_key():
    key = secrets.token_hex(64)
    print("Your SECRET_KEY:")
    print(key)
    return key



def generate_secret_key_b64():
    raw = secrets.token_bytes(64)
    key = base64.urlsafe_b64encode(raw).decode()
    print("Your Base64 SECRET_KEY:")
    print(key)
    return key

if __name__ == "__main__":
    generate_secret_key()