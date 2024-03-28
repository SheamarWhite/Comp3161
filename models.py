
from werkzeug.security import generate_password_hash

class UserProfile():

    def __init__(self,id, firstname, lastname, type):
        self.id = id
        self.firstname = firstname
        self.lastname = lastname
        self.type = type
      
        
    def is_authenticated(self):
        if self.id == -4:
            return False
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicodedata(self.id)  # python 2 support
        except NameError:
            return str(self.id)  # python 3 support

    def __repr__(self):
        return '<User %r>' % (self.firstname)