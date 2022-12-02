from db import db
from db import User

def get_user_by_netid(netid):
    """
    Returns the user based on the netid
    """
    return User.query.filter(User.netid == netid).first()

def get_user_by_session_token(session_token):
    """
    Returns the user based on the session token
    """
    return User.query.filter(User.session_token == session_token).first()

def get_user_by_update_token(update_token):
    """
    Returns the user based on the update token
    """
    return User.query.filter(User.update_token == update_token).first()

def verify_credentials(netid,password):
    """
    Returns true if the credentials match
    """

    user_exists = get_user_by_netid(netid)
    
    if user_exists is None:
        return False, None
    
    return user_exists.verify_password(password), user_exists
    

def create_user(college, major, class_year, name, netid, password):
    """
    Creates a User object in the database

    Returns False if it exist, True if it does not
    """

    user_exist = get_user_by_netid(netid)
    
    if user_exist is not None:
        return False, user_exist
    
    user = User(college = college, 
                major = major, 
                class_year = class_year,
                name = name,
                netid = netid,
                password= password
    )
    db.session.add(user)
    db.session.commit()
    return True, user

def renew_session(update_token):
    """
    """
    user_exists = get_user_by_update_token(update_token)

    if user_exists is None:
        return False, user_exists

    user_exists.renew_sessions()
    db.session.commit()
    return True, user_exists
