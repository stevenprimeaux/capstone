from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv, find_dotenv
from os import environ
from six.moves.urllib.parse import urlencode

from .auth import AuthError, requires_auth, requires_scope

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

def create_app(test_config=None):

    # configuration

    DB_U = environ.get('DB_U')
    DB_P = environ.get('DB_P')
    DB_H = environ.get('DB_H')

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=environ.get('SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI=f'postgresql://{DB_U}:{DB_P}@{DB_H}/openschool',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    db = SQLAlchemy(app)

    # auth

    AUTH0_DOMAIN = environ.get('AUTH0_DOMAIN')
    AUTH0_CLIENT_ID = environ.get('AUTH0_CLIENT_ID')
    AUTH0_CLIENT_SECRET = environ.get('AUTH0_CLIENT_SECRET')
    AUTH0_CALLBACK_URL = environ.get('AUTH0_CALLBACK_URL')
    AUTH0_AUDIENCE = environ.get('AUTH0_AUDIENCE')

    AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN

    oauth = OAuth(app)

    auth0 = oauth.register(
        'auth0',
        client_id=AUTH0_CLIENT_ID,
        client_secret=AUTH0_CLIENT_SECRET,
        api_base_url=AUTH0_BASE_URL,
        access_token_url=AUTH0_BASE_URL + '/oauth/token',
        authorize_url=AUTH0_BASE_URL + '/authorize',
        client_kwargs={
            'scope': 'email get:students get:students-1 get:students-2 post:school modify:school'
        }
    )

    # models

    class Student(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80), unique=True, nullable=False)
        address = db.Column(db.String(80), unique=True, nullable=False)
        school_id = db.Column(
            db.Integer,
            db.ForeignKey('school.id'),
            nullable=False
        )
        school = db.relationship(
            'School',
            backref=db.backref('students', lazy=True)
        )

        def format(self):
          return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'school': self.school.name
          }

    class School(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80), unique=True, nullable=False)
        address = db.Column(db.String(80), unique=True, nullable=False)

        def format(self):
          return {
            'id': self.id,
            'name': self.name,
            'address': self.address
          }

    # records for testing

    try:
        db.drop_all()
    except:
        pass

    try:
        db.create_all()
    except:
        pass

    school_1 = School(name='School Name 1', address='1 School Street')
    school_2 = School(name='School Name 2', address='2 School Street')
    student_1 = Student(name='Student 1', address='1 Main Street', school_id=1)
    student_2 = Student(name='Student 2', address='2 Main Street', school_id=1)
    student_3 = Student(name='Student 3', address='3 Main Street', school_id=2)
    student_4 = Student(name='Student 4', address='4 Main Street', school_id=2)
    db.session.add(school_1)
    db.session.add(school_2)
    db.session.add(student_1)
    db.session.add(student_2)
    db.session.add(student_3)
    db.session.add(student_4)
    db.session.commit()

    # endpoints

    # auth

    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/login')
    def login():
        return auth0.authorize_redirect(
            redirect_uri=AUTH0_CALLBACK_URL,
            audience=AUTH0_AUDIENCE
        )

    @app.route('/callback')
    def callback_handling():
        session['jwt'] = auth0.authorize_access_token()['access_token']
        return redirect('/content')

    @app.route('/content')
    def content():
        if 'jwt' not in session:
            return redirect('/')
        return render_template('content.html', data=session)

    @app.route('/logout')
    def logout():
        session.clear()
        params = {
            'returnTo': url_for('home', _external=True),
            'client_id': AUTH0_CLIENT_ID
        }
        print(auth0.api_base_url + '/v2/logout?' + urlencode(params))
        return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))

    # schools

    @app.route('/schools', methods=['GET'])
    def get_schools():
        return {'schools': [i.format() for i in School.query.all()]}

    @app.route('/schools', methods=['POST'])
    @requires_auth
    def post_school():
        if requires_scope('post:school'):
            r = request.json
            school = School(name=r['name'], address=r['address'])
            db.session.add(school)
            db.session.commit()
            return r
        raise AuthError({
            "code": "unauthorized",
            "description": "You don't have permission to access this resource."
        }, 403)

    @app.route('/schools/<int:school_id>', methods=['PATCH', 'DELETE'])
    @requires_auth
    def modify_school(school_id):
        if requires_scope('modify:school'):
            if request.method == 'PATCH':
                r = request.json
                school = School.query.get(school_id)
                school.name = r['name']
                school.address = r['address']
                db.session.commit()
                return {'school': school.format()}
            if request.method == 'DELETE':
                school = School.query.get(school_id)
                if len(school.students) > 0:
                    abort(405)
                db.session.delete(school)
                db.session.commit()
                return {'school_id': school_id}
        raise AuthError({
            "code": "unauthorized",
            "description": "You don't have permission to access this resource."
        }, 403)

    # students

    @app.route('/students', methods=['GET'])
    @requires_auth
    def get_students():
        if requires_scope('get:students'):
            students = [
                i.format() for i in Student.query.all()
            ]
            return {'students': students}
        raise AuthError({
            "code": "unauthorized",
            "description": "You don't have permission to access this resource."
        }, 403)

    @app.route('/schools/<int:school_id>/students', methods=['GET'])
    @requires_auth
    def get_students_school(school_id):
        if \
        requires_scope('get:students') or \
        requires_scope(f'get:students-{school_id}'):
            students = [
                i.format() for i in Student.query.filter_by(school_id=school_id)
            ]
            return {'students': students}
        raise AuthError({
            "code": "unauthorized",
            "description": "You don't have permission to access this resource."
        }, 403)

    # errors

    @app.errorhandler(AuthError)
    def handle_auth_error(ex):
        response = jsonify(ex.error)
        response.status_code = ex.status_code
        return response



    return app
