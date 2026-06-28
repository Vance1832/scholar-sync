from flask import render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from ..services.auth import register_user, authenticate


@auth.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for(f"{current_user.role}.dashboard"))
    return redirect(url_for("auth.login"))


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f"{current_user.role}.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")

        user = authenticate(username, password, role)
        if user:
            login_user(user, remember=request.form.get("remember") == "on")
            next_page = request.args.get("next")
            return redirect(next_page or url_for(f"{role}.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for(f"{current_user.role}.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        role = request.form.get("role", "student")

        if role not in ("student", "donor"):
            flash("Invalid role selected.", "danger")
            return render_template("auth/register.html")

        ok, msg = register_user(username, password, confirm, role)
        if ok:
            flash(msg, "success")
            return redirect(url_for("auth.login"))
        flash(msg, "danger")

    return render_template("auth/register.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
