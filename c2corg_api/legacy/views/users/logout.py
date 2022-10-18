from flask_camp.views.account import user_login


rule = "/users/logout"


post = user_login.delete
