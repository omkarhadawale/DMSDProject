from flask_bcrypt import Bcrypt

bycrypt = Bcrypt()
password = 'bond123'
hash = bycrypt.generate_password_hash(password)
print(hash)