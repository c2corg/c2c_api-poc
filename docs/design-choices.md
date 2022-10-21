## Why Flask ?

[Django](https://github.com/django/django) is by far the most popular python web framework. But it meant to build full HTTP app, from ORM, bakend, to front-end. It handles thousand of aspects we don't need for a REST API. And it's API is more complex, with a steepest learnign curve.

[Flask](https://github.com/pallets/flask) is way simpler to learn, and support out-of-the box REST API feature. And it's the second mosat popular python web framework, with a gentle learning curve, with no complex abstraction. Go for it !

## Why a custom extension

Because I did not found something that fit our needs : 

* Headless wiki API
* Versionning
* Reasonnably used 
* Configuration in text files (not an admin interface where we can't follow what's done)
* SGIS capabilities

## User names

v6 user model introduces 4 differents user identifiers : 

* email: unique
* name: a label used on topoguide, not unique
* username: used only to log-in, unique, and private (no one can see it, even moderators)
* forum_username: the forum user name, unique

It comes with two major issues : 

1. Needless complexity. We got a lot of request for login issue bacause user do not remember their `username`
2. Community complexity to identify a person. if `forum_username` != `name`, it's hard to make the link between a person in the forum, and the person in the topoguide.

In the new model, there will be only to identifiers : 

* email, unique
* name, unique, used for both forum and topoguide. Will be filled by V6 `forum_username`

It'll simplify the login failure questions, make a better link between topoguide and forum, allow mention in markdown. 

For now, v6 name (the label) is saved in `User.ui_preference["full_name"]`, but may be removed (it it exists, it wiull be in profile). And v6 `username` will be totally dropped.

Oall of this can be resumed by :

| v6 property    | Unique    | Public    | v6 usage          | v7 property               | v7 usage                       
| --             | --        | --        | --                | --                        | --                             
| username       | Yes       | No        | log-in            | N/A                       | N/A
| name           | No        | Yes       | topoguide label   | ui_prefences["full_name"] | Just to pass the legacy test, to be dropped                             
| forum_username | Yes       | Yes       | forum label       | name                      | login, topo label, forum label 
| email          | Yes       | No        | send email        | email                     | login, send email
