import re
import os
import pydantic

from flask import Flask, jsonify
from flask import request
from flask.views import MethodView

from flask_bcrypt import Bcrypt
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
from typing import Union

app = Flask('app')
# PG_DSN = 'postgresql://admin:1234@localhost:5433/flask_netology'
# engine = create_engine(PG_DSN)
engine = create_engine(os.getenv("PG_DSN"))
Base = declarative_base()

Session = sessionmaker(bind=engine)
bcrypt = Bcrypt(app)

password_regex = re.compile(
    "^(?=.*[a-z_])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&_])[A-Za-z\d@$!#%*?&_]{8,200}$"
)
email_regex = '^[a-z]([\w-]*[a-z]|[\w-.]*[a-z]{2,}|[a-z])*@[a-z]([\w-]*[a-z]|[\w-.]*[a-z]{2,}|[a-z]){4,}?\.[a-z]{2,}$'

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String(45), nullable=False, unique=True)
    user_name = Column(String(40), nullable=False)
    password = Column(String(500), nullable=False)
    registration_time = Column(DateTime, server_default=func.now())
    advertisement = relationship("Advertisement")


class Advertisement(Base):
    __tablename__ = "advertisement"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(5000), nullable=False)
    creation_time = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("user.id"))
    

Base.metadata.create_all(engine)


class HTTPError(Exception):
    def __init__(self, status_code: int, message: Union[str, list, dict]):
        self.status_code = status_code
        self.message = message


@app.errorhandler(HTTPError)
def handle_invalid_usage(error):
    response = jsonify({"message": error.message})
    response.status_code = error.status_code
    return response

class UserValidator(pydantic.BaseModel):
    email: str
    user_name: str
    password: str

    @pydantic.validator("password")
    def strong_password(cls, value: str):
        if not re.search(password_regex, value):
            raise ValueError("password to easy")

        return value

class AdvertismentValidator(pydantic.BaseModel):
    title: str
    description : str
    user_id = int


def validate(unvalidated_data: dict, validation_model):
    try:
        return validation_model(**unvalidated_data).dict()
    except pydantic.ValidationError as er:
        raise HTTPError(400, er.errors())

@app.route("/get_users/", methods=["GET"])
def get_users():
    with Session() as session:
        users = session.query(User)  
        result = session.execute(users).scalars().all()  

        data = [{
            'id': res.id, 
            'email': res.email, 
            'user_name': res.user_name,
            'registration_date': res.registration_time.date()} for res in result]

        return jsonify(data)


class UserView(MethodView):
    
    def get(self, user_id: int):
        with Session() as session:
            res = session.query(User).filter(User.id==user_id).first()  

            if not res:
                raise HTTPError(404, "user not found") 

            return jsonify({
                'id': res.id, 
                'email': res.email, 
                'user_name': res.user_name,
                'registration_date': res.registration_time.date()})


    def post(self):
        new_user_data = request.json
        with Session() as session:
            new_user = User(email=new_user_data['email'],user_name=new_user_data['user_name'], password=new_user_data['password'])
            session.add(new_user)
            session.commit()
            return jsonify({
                'id': new_user.id
            })

  
@app.route("/get_advertisments/", methods=["GET"])
def get_advertisments():
    params = request.args
    with Session() as session:
        if params.get('user_id'):
            user_id = params.get('user_id')
            result = session.query(Advertisement).filter(
                Advertisement.user_id == user_id).all()
        else:
            result = session.query(Advertisement).all()
           
        data = []
        for res in result:
            user = session.query(User).filter(User.id==res.user_id).first()
            user_data ={
                'id': user.id, 
                'email': user.email, 
                'user_name': user.user_name,
                'registration_date': user.registration_time.date()}

            data.append({
            'id': res.id, 
            'title': res.title, 
            'description': res.description,
            'user_id': res.user_id,
            'user': user_data,
            'creation_date': res.creation_time.date()})
        return jsonify(data)

@app.route("/del_advertisments/<int:adv_id>/", methods=["DELETE"])
def dell(adv_id):
    with Session() as session:
        adv = session.query(Advertisement).filter(Advertisement.id==adv_id).first()
        if adv:
            session.delete(adv)
            session.commit()
            return jsonify({
                'id': adv.id
            })
        else:
            raise HTTPError(404, "advertisment not found") 


class AdvertismentsView(MethodView):

    def post(self):
        with Session() as session:
            data = request.json
            adv = Advertisement(title=data['title'], description=data['description'], user_id=data['user_id'])        
            session.add(adv)
            session.commit()
            return jsonify({
                'id': adv.id, 
                'title': adv.title, 
                'description': adv.description,
            })
    


app.add_url_rule('/user/<int:user_id>/', view_func=UserView.as_view('g_user'), methods=["GET"])
app.add_url_rule('/add_user/', view_func=UserView.as_view('p_user'), methods=["POST"])


app.add_url_rule('/add_adv/', view_func=AdvertismentsView.as_view('a_adv'), methods=["POST"])

