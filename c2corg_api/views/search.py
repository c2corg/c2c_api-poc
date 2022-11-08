from flask_camp import allow

rule = "/search"


@allow("anonymous", "authenticated")
def get():
    # TODO ...
    return {"articles": {"total": 666}}
