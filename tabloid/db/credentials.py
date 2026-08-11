import keyring

def save_password(connection_id, password):
    keyring.set_password("tabloid", connection_id, password)

def get_password(connection_id):
    return keyring.get_password("tabloid", connection_id)

def delete_password(connection_id):
    keyring.delete_password("tabloid", connection_id)

def has_password(connection_id):
    return bool(get_password(connection_id))