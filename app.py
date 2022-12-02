import json
import os
from db import db
from flask import Flask 
from db import Course
from db import Post
from db import User
from flask import request
import users_dao
import datetime


app = Flask(__name__)
db_filename = "chat.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.create_all()

def success_response(data, code=200):
    """
    Helper function that gives the success response to the request
    """
    return json.dumps(data), code


def failure_response(message, code=404):
    """
    Helper function that gives the failure response to the request
    """
    return json.dumps({"error": message}), code

def extract_token(request):
    """
    Helper function that extracts the token from the header of a request
    """
    autherization_header = request.headers.get("Authorization")
    if autherization_header is None:
        return False, failure_response("Missing authorization header", 400)
    
    bearer_token = autherization_header.replace("Bearer", "").strip()
    if bearer_token is None or not bearer_token:
        return False, failure_response("Invalid authorization header", 400)
    return True, bearer_token

#------Courses Routes------------------------------------------------------------


@app.route("/")
@app.route("/api/courses/")
def get_courses():
    """
    Endpoint for getting all courses
    """
    courses = [course.serialize() for course in Course.query.all()]
    return success_response({"courses":courses})

@app.route("/api/courses/", methods=["POST"])
def create_courses():
    """
    Endpoint for creating a new course 
    """
    body = json.loads(request.data)
    code= body.get("code")
    name = body.get("name")
    if code is None or name is None:
        return failure_response("Course not found",400)
    new_course = Course(code = code, name = name )
    db.session.add(new_course)
    db.session.commit()
    return success_response(new_course.serialize(),201)

@app.route("/api/courses/<int:course_id>/")
def get_course(course_id):
    """
    Endpoint for getting a course by id
    """
    course = Course.query.filter_by(id = course_id).first()
    if course is None:
        return failure_response("Course not found")
    return success_response(course.serialize())

@app.route("/api/courses/<int:course_id>/", methods=["DELETE"])
def delete_course(course_id):
    """
    Endpoint for deleting a course by id
    """
    course = Course.query.filter_by(id = course_id).first()
    if course is None:
        return failure_response("Course not found")
    db.session.delete(course)
    db.session.commit()
    return success_response(course.serialize())

# -- Comments Routes ---------------------------------------------------


@app.route("/api/courses/<int:course_id>/post/", methods=["POST"])
def create_post(course_id):
    """
    Endpoint for creating a comment for a course by id
    """
    course = Course.query.filter_by(id = course_id).first()
    if course is None:
        return failure_response("Course not found")
    body = json.loads(request.data)
    comment = body.get("comment")
    if comment is None:
        return failure_response("Could not create comment", 400)

    new_post = Post(
        comment = comment,
        course_id = course_id
    )
    db.session.add(new_post)
    db.session.commit()
    return success_response(new_post.serialize(), 201)

@app.route("/api/courses/<int:course_id>/post/<int:post_id>/")
def get_post(course_id,post_id):
    course = Course.query.filter_by(id = course_id).first()
    if course is None:
        return failure_response("Course not found")
    post = Post.query.filter_by(id = post_id).first()
    if post is None:
        return failure_response("Comment not found")
    return success_response(post.simple_serialize())

@app.route("/api/courses/<int:course_id>/post/<int:post_id>/", methods=["DELETE"])
def delete_post(course_id,post_id):
    """
    Endpoint for deleting a course by id
    """
    course = Course.query.filter_by(id = course_id).first()
    if course is None:
        return failure_response("Course not found")
    post = Post.query.filter_by(id = post_id).first()
    if post is None:
        return failure_response("Comment not found")
    db.session.delete(post)
    db.session.commit()
    return success_response(post.simple_serialize())


# -- User/student/instructor Routes --------------------------------------------------

#First Part is creating, registering and getting the user
@app.route("/api/register/", methods=["POST"])
def register_user():
    """
    Endpoint for registering a user
    """
    body = json.loads(request.data)
    college = body.get("college")
    major = body.get("major")
    class_year = body.get("class_year")
    name = body.get("name")
    netid = body.get("netid")
    password = body.get("password")
    if name == None or netid == None or college is None:
        if major is None or class_year is None or password is None:
            return failure_response("Missing informartion", 400)
    success, user = users_dao.create_user(
        college, major, class_year, name, netid, password
    )

    if not success:
        return failure_response("Users already exists", 400)
    
    return success_response(
        {
            "session_token": user.session_token,
            "session_expiration":str(user.session_expiration),
            "update_token": user.update_token
        }
    )
    
@app.route("/api/user/<int:user_id>/")
def get_user(user_id):
    """
    Endpoint for getting a user by id
    """
    user = User.query.filter_by(id = user_id).first()
    if user is None:
        return failure_response("User not found")
    return success_response(user.serialize())


# Next part is the user to update his account/courses and loging in/out
@app.route("/api/user/edit/", methods = ["POST"])
def update_user_info():
    """
    Endpoint for verifying a session token and returning
    """
    success, session_token = extract_token(request)

    if not success:
        return failure_response("Could not extract session token",400)
    
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token", 400)

    body = json.loads(request.data)
    user.college =  body.get("college", user.college)
    user.major =  body.get("major", user.major)
    user.class_year = body.get("class_year", user.class_year)
    user.name = body.get("name", user.name)
    db.session.commit()

    if user.college.strip() is None or user.major. strip() is None:
        if user.class_year.strip() is None or user.name.strip() is None:
            return failure_response("Missing information, please try again", 400)
    
    return success_response({"message": "You have successfully implemented sessions!"})

@app.route("/api/user/<int:course_id>/add/", methods=["POST"])
def enroll_user(course_id):
    """
    Endpoint for updating a user by id/ putting a user into ta or student
    """
    success, session_token = extract_token(request)

    if not success:
        return failure_response("Could not extract session token",400)
    
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token", 400)

    course = Course.query.filter_by(id = course_id).first()
    if course is None:
        return failure_response("Course not found")
    body = json.loads(request.data)

    type = body.get("type")

    if user is None:
        return failure_response("User not found")
    if user in course.banned_students:
        return failure_response("User was banned from server", 400)
    if type == "student":
        course.students.append(user)
        db.session.commit()
        return success_response(course.serialize())
    elif type == "ta":
        course.ta_s.append(user)
        db.session.commit()
        return success_response(course.serialize())
    else:
        return failure_response("Did not choose between student or instructor")

@app.route("/api/courses/<int:course_id>/ban/", methods=["POST"])
def dev_ban_students(course_id):
    """
    Enpoint for a Dev banning a student from a course
    """
    success, session_token = extract_token(request)

    if not success:
        return failure_response("Could not extract session token",400)
    
    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token) or user.netid != os.environ.get("NETID"):
        return failure_response("Invalid session token", 400)

    course = Course.query.filter_by(id = course_id).first()
    if course is None:
        return failure_response("Course not found")
    body = json.loads(request.data)
    user_id = body.get("user_id")
    other_user = User.query.filter_by(id = user_id).first()
    if other_user is None:
        return failure_response("User not found!")
    if other_user in course.students:
        course.students.remove(other_user)
    if other_user in course.ta_s:
        course.ta_s.remove(other_user)
    course.banned_students.append(other_user)
    db.session.commit()
    return success_response(course.serialize())

@app.route("/login/", methods= ["POST"])
def login():
    """
    Endpoin for logging in a user
    """
    body = json.loads(request.data)
    netid = body.get("netid")
    password = body.get("password")

    if netid is None or password is None:
        return failure_response("missing netid or password!", 400)
    
    success, user = users_dao.verify_credentials(netid,password)

    if not success:
        return failure_response("Incorrect netid or password", 401)
    
    return success_response(
        {
            "session_token": user.session_token,
            "session_expiration":str(user.session_expiration),
            "update_token": user.update_token
        } 
    )
@app.route("/session/", methods= ["POST"])
def update_session():
    """
    Updates the token session
    """
    success, update_token = extract_token(request)

    if not success:
        return failure_response("Could not extract update token", 401)

    success_user, user = users_dao.renew_session(update_token)

    if not success_user:
        return failure_response("Invalid update token", 400)

    return success_response(
        {
            "session_token": user.session_token,
            "session_expiration":str(user.session_expiration),
            "update_token": user.update_token
        } 
    )

@app.route("/logout/", methods= ["POST"])
def logout():
    """
    """
    success, session_token = extract_token(request)

    if not success:
        return failure_response("Could not extract session token", 401)

    user = users_dao.get_user_by_session_token(session_token)
    if user is None or not user.verify_session_token(session_token):
        return failure_response("Invalid session token", 400)
    
    user.session_token = ""
    user.session_expiration = datetime.datetime.now()
    user.update_token = ""
    db.session.commit()
   
    return success_response({"message": "You have successfully logged out"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

