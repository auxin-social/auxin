from flask_login import LoginManager, UserMixin

import hashlib

# cyber security god please forgive me...
PASSWORDS = {
    "ash": "66483810b72db7712a5bbd7642bb20f2f29bb67e645b7fe471d0be0296be25efd2cc4041bd98ef477365c0e0768847277db58ac5e0a00383ee791fbfd1052618"
}
IDS = {
    "ash": '1'
}

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id 

    def get(user_id):
        if user_id in IDS.values():
            return User(user_id)
        else:
            return None

    def login_user(username, password):
        if username not in PASSWORDS:
            return None
        
        hashed_password = hashlib.sha512(password.encode('utf-8')).hexdigest()        
        if hashed_password != PASSWORDS[username]:
            return None

        return User(IDS[username])
