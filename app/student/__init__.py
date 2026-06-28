from flask import Blueprint

student = Blueprint("student", __name__, template_folder="../templates/student")

from . import routes  # noqa: E402, F401
