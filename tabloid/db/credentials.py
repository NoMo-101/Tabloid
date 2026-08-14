import keyring

APP_NAME = "tabloid"

def save_password(connection_id, password):
    """Saves or updates a password in the system keyring for a given connection"""
    keyring.set_password(APP_NAME, connection_id, password)

def get_password(connection_id):
    """Returns the password string, or None if it doesn't exist."""
    return keyring.get_password(APP_NAME, connection_id)

def delete_password(connection_id):
    """Deletes a stored password by connection_id."""
    keyring.delete_password(APP_NAME, connection_id)

def has_password(connection_id):
    """Returns True if a password exists for the connection_id, False otherwise."""
    return bool(get_password(connection_id))