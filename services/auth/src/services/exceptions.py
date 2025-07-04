class BadEmailException(Exception):
    pass

class EmailExistException(Exception):
    pass

class UsernameExistException(Exception):
    pass

class RoleExistException(Exception):
    pass

class UserExistException(Exception):
    pass

class BadCredsException(Exception):
    pass

class BadPermissionsException(Exception):
    pass

class UnauthorizedException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

class RoleNotFoundException(Exception):
    pass