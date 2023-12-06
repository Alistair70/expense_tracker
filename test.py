import jwt

def encode(user_id):
    payload = {
        'sub': user_id
    }
    return jwt.encode(payload, "123456" ,algorithm='HS256')

def decode(payload):
    decoded_payload = jwt.decode(payload, "123456" , algorithms=['HS256'])
    return decoded_payload




token = encode(1000)
print(token)
print(type(token))
decoded_token = decode(token)
print(type(decoded_token['sub']))

