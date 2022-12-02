from flask_sqlalchemy import SQLAlchemy
import datetime
import hashlib
import bcrypt
import os

db = SQLAlchemy()
ta_table = db.Table(
    "association",
    db.Column("course_id", db.Integer,db.ForeignKey("courses.id")),
    db.Column("user_id", db.Integer,db.ForeignKey("users.id"))

)


student_table = db.Table(
    "association2",
    db.Column("course_id", db.Integer,db.ForeignKey("courses.id")),
    db.Column("user_id", db.Integer,db.ForeignKey("users.id"))
)

banned_table = db.Table(
    "association3",
    db.Column("course_id", db.Integer,db.ForeignKey("courses.id")),
    db.Column("user_id", db.Integer,db.ForeignKey("users.id"))
)


class Course(db.Model):
    """
    Has a 1 to many relationship with Posts
    Has a many to many relationship with User 
    """
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    code = db.Column(db.String, nullable = False)
    name = db.Column(db.String, nullable = False)
    posts = db.relationship("Post", backref = "courses", cascade = "delete")
    ta_s = db.relationship("User", secondary = ta_table, back_populates ="ta_courses")
    students = db.relationship("User", secondary = student_table, back_populates ="student_courses")
    banned_students = db.relationship("User",secondary = banned_table,back_populates ="banned_student_courses")


    def __init__(self, **kwargs):
        """
        Initializes Course object
        """
        self.code = kwargs.get("code", "")
        self.name = kwargs.get("name", "")


    def serialize(self):
        
        """
        Serializes a Course object
        """
        return{
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "posts": [p.simple_serialize() for p in self.posts],
            "ta_s":[t.simple_serialize() for t in self.ta_s],
            "students": [s.simple_serialize() for s in self.students],
            "banned_students": [b.simple_serialize() for b in self.banned_students]
        }


    def simple_serialize(self):

        """
        Simple Serializes a Course object so infinte loop does not occur
        """

        return{
            "id": self.id,
            "code": self.code,
            "name": self.name
            
        }


class Post(db.Model):
    """
    Post model has a many to one relationship with Course
    """
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    comment = db.Column(db.String, nullable = False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable = False)
    
    
    

    def __init__(self, **kwargs):
        """
        Initializes Post object
        """
        self.comment = kwargs.get("comment", "")
        self.course_id = kwargs.get("course_id")
        
        

    def serialize(self):
        
        """
        Serializes a Post object
        """

        return{
            "id": self.id,
            "comment": self.comment,
            "course": Course.query.filter_by(id = self.course_id).first().simple_serialize()
        }


    def simple_serialize(self):
        
        """
        Simple Serializes a Post object so infinte loop does not occur
        """

        return{
            "id": self.id,
            "comment": self.comment,

        }


class User(db.Model):
    """
    User Model
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    college = db.Column(db.String, nullable = False)
    major = db.Column(db.String, nullable = False)
    class_year = db.Column(db.String, nullable = False)
    name = db.Column(db.String, nullable = False)
    netid = db.Column(db.String, nullable = False)
    password_digest = db.Column(db.String, nullable = False)

    ta_courses = db.relationship("Course", secondary = ta_table, back_populates = "ta_s")
    student_courses = db.relationship("Course", secondary = student_table, back_populates = "students")
    banned_student_courses = db.relationship("Course",secondary = student_table,back_populates = "banned_students")
    
    #authentication
    session_token = db.Column(db.String, nullable = False, unique = True)
    session_expiration = db.Column(db.DateTime, nullable = False)
    update_token = db.Column(db.String, nullable = False, unique = True)

    def __init__(self, **kwargs):
        """
        Inititalizes a User object
        """
        self.college = kwargs.get("college", "")
        self.major = kwargs.get("major", "")
        self.class_year = kwargs.get("class_year", "")
        self.name = kwargs.get("name", "")

        self.netid = kwargs.get("netid", "")
        self.password_digest = bcrypt.hashpw(kwargs.get("password").encode("utf8"), bcrypt.gensalt(rounds=13))
        self.renew_sessions()
    
    def _urlsafe_base_64(self):
        """
        Randomly generates a hashed token for sessions
        """
        return hashlib.sha1(os.urandom(64)).hexdigest()

    def renew_sessions(self):
        """
        Renews the session
        """
        self.session_token = self._urlsafe_base_64()
        self.session_expiration = datetime.datetime.now() + datetime.timedelta(days=180)
        self.update_token = self._urlsafe_base_64()
    
    def verify_password(self,password):
        """
        Verifies the password
        """
        return bcrypt.checkpw(password.encode("utf8"),self.password_digest)

    def verify_session_token(self,session_token):
        """
        Verifies the session token
        """
        return session_token == self.session_token and datetime.datetime.now() < self.session_expiration

    def verify_update_token(self,update_token):
        """
        Verifies the update token of a user
        """
        return update_token == self.update_token

    def serialize(self):
        """
        Simple serialize User object
        """

        return{
            "id": self.id,
            "name": self.name,
            "college":self.college,
            "major": self.major,
            "class_year": self.class_year,
            "courses" : [t.simple_serialize() for t in self.ta_courses + self.student_courses\
                + self.banned_student_courses]
        }

    def simple_serialize(self):
        """
        Simple Serializes a User object so infinte loop does not occur
        """ 
        return{
            "id": self.id,
            "name": self.name,
            "college":self.college,
            "major": self.major,
            "class_year": self.class_year

        }

    
