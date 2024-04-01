from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import jwt
import re
from datetime import datetime, timedelta


DB_CONFIG='mysql+pymysql://root:N4j1n4j1@localhost:3306/course_quest'
app = Flask(__name__)
ma = Marshmallow(app)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONFIG
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
SECRET_KEY = "b'|\xe7\xbfU3`\xc4\xec\xa7\xa9zf:}\xb5\xc7\xb9\x139^3@Dv'"

def create_token(user_id):
    payload = {
        'exp': datetime.utcnow() + timedelta(days=4),
        'iat': datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.Enum('student', 'professor'), nullable=False)

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "name" , "email", "password", "user_type")
        model = User

user_schema = UserSchema()

@app.route('/user', methods=['POST'])
def create_user():
    try:
        user_name = request.json['user_name']
        email = request.json['email']
        password = request.json['password']
        user_type = request.json['user_type']

        if user_name is None or password is None or email is None or user_type is None:
            error_response = {
                'error': 'Username, Password and User Type cannot be empty',
                'status_code': 400
            }
            return jsonify(error_response), 400

        if not re.match(r'^[a-zA-Z0-9._%+-]+@(gmail\.com|hotmail\.com|yahoo\.com|mail\.aub\.edu)$', email):
            error_response = {
                'error': 'Enter a valid email address with domain @gmail.com, @hotmail.com, @yahoo.com, or @mail.aub.edu',
                'status_code': 400
            }
            return jsonify(error_response), 400


        if user_type!='student' and user_type!='professor':
            error_response = {
                'error': 'Enter valid user type',
                'status_code': 400
            }
            return jsonify(error_response), 400
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            error_response = {
                'error': 'Invalid username or password',
                'status_code': 400
            }
            return jsonify(error_response), 400



        new_user = User(
            name=user_name,
            email=email,
            password=password,
            user_type= user_type
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify(user_schema.dump(new_user)), 201

    except Exception as e:

        return jsonify({"error": f"Error: {str(e)}"}), 500

@app.route('/authentication', methods=['POST'])
def authenticate_user():

    try:
        user_name_email = request.json['user_name']

        password = request.json['password']

        if (user_name_email is None ) or password is None:
            abort(400, 'Username and Password cannot be empty')

        existing_user = User.query.filter_by(name=user_name_email).first()
        existing_email = User.query.filter_by(email=user_name_email).first()
        if not existing_user and not existing_email:
            abort(403, 'Wrong username or password 1')

        if not existing_user.password == password:
            abort(403, 'Wrong username or password 2')

        token = create_token(existing_user.id)

        return jsonify({"token": str(token)}), 201

    except Exception as e:

        return jsonify({"error": f"Error: {str(e)}"}), 500


# Create database tables

if __name__ == '__main__':
    app.run(debug=True)
