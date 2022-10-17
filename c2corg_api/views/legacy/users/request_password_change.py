from flask_camp.views.account import reset_password


rule = "/users/request_password_change"

post = reset_password.post
