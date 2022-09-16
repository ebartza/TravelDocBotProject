# Module file: my_rasa_config.py
# basic database & email configuration

config = {
    'host': 'localhost',
    'user': 'root',            # Mysql user
    'password': 'root',        # Password for Mysql user
    'database':'cpsv_ap',
    'auth_plugin':'mysql_native_password'
}

email_settings = {
    'LOGIN_EMAIL' : "passbot.chatbot@gmail.com",
    'PASSWORD' : "passbot200!",
    'SENDER_EMAIL' : "passbot.chatbot@gmail.com"  
}

#LOGIN_EMAIL = "passbot.chatbot@gmail.com"
#PASSWORD = "passbot200!" 
#SENDER_EMAIL = "passbot.chatbot@gmail.com"  