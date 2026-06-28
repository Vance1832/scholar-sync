from flask import Blueprint

donor = Blueprint("donor", __name__, template_folder="../templates/donor")

from . import routes  # noqa: E402, F401
