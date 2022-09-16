# Module file: my_rasa_config.py
# basic database & email configuration

config = {
    'host': 'localhost',
    'user': 'root',            # Mysql user
    'password': 'Gesdoi!@34',        # Password for Mysql user
    'database':'cpsv_ap',
    'auth_plugin':'caching_sha2_password'
}

LOGIN_EMAIL = ""
PASSWORD = "" 
SENDER_EMAIL = ""  