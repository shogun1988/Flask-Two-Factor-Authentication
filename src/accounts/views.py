from src.utils import get_b64encoded_qr_image
from .forms import LoginForm, RegisterForm, TwoFactorForm, ForgotPasswordForm, ResetPasswordForm
from src.accounts.models import User
from src import db, bcrypt, app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import uuid
from flask_login import current_user, login_required, login_user, logout_user
from flask import Blueprint, flash, redirect, render_template, request, url_for

accounts_bp = Blueprint("accounts", __name__)

HOME_URL = "core.home"
SETUP_2FA_URL = "accounts.setup_two_factor_auth"
VERIFY_2FA_URL = "accounts.verify_two_factor_auth"
FORGOT_PASSWORD_URL = "accounts.forgot_password"
RESET_PASSWORD_URL = "accounts.reset_password"


@accounts_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        if current_user.is_two_factor_authentication_enabled:
            flash("You are already registered.", "info")
            return redirect(url_for(HOME_URL))
        else:
            flash(
                "You have not enabled 2-Factor Authentication. Please enable first to login.", "info")
            return redirect(url_for(SETUP_2FA_URL))
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()

            login_user(user)
            flash("You are registered. You have to enable 2-Factor Authentication first to login.", "success")

            return redirect(url_for(SETUP_2FA_URL))
        except Exception:
            db.session.rollback()
            flash("Registration failed. Please try again.", "danger")

    return render_template("accounts/register.html", form=form)


@accounts_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_two_factor_authentication_enabled:
            flash("You are already logged in.", "info")
            return redirect(url_for(HOME_URL))
        else:
            flash(
                "You have not enabled 2-Factor Authentication. Please enable first to login.", "info")
            return redirect(url_for(SETUP_2FA_URL))
        
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, request.form["password"]):
            login_user(user)
            if not current_user.is_two_factor_authentication_enabled:
                flash(
                    "You have not enabled 2-Factor Authentication. Please enable first to login.", "info")
                return redirect(url_for(SETUP_2FA_URL))
            return redirect(url_for(VERIFY_2FA_URL))
        elif not user:
            flash("You are not registered. Please register.", "danger")
        else:
            flash("Invalid username and/or password.", "danger")
    return render_template("accounts/login.html", form=form)


@accounts_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You were logged out.", "success")
    return redirect(url_for("accounts.login"))


@accounts_bp.route("/setup-2fa")
@login_required
def setup_two_factor_auth():
    secret = current_user.secret_token
    uri = current_user.get_authentication_setup_uri()
    base64_qr_image = get_b64encoded_qr_image(uri)
    return render_template("accounts/setup-2fa.html", secret=secret, qr_image=base64_qr_image)


@accounts_bp.route("/verify-2fa", methods=["GET", "POST"])
@login_required
def verify_two_factor_auth():
    form = TwoFactorForm(request.form)
    if form.validate_on_submit():
        if current_user.is_otp_valid(form.otp.data):
            if current_user.is_two_factor_authentication_enabled:
                flash("2FA verification successful. You are logged in!", "success")
                return redirect(url_for(HOME_URL))
            else:
                try:
                    current_user.is_two_factor_authentication_enabled = True
                    db.session.commit()
                    flash("2FA setup successful. You are logged in!", "success")
                    return redirect(url_for(HOME_URL))
                except Exception:
                    db.session.rollback()
                    flash("2FA setup failed. Please try again.", "danger")
                    return redirect(url_for(VERIFY_2FA_URL))
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return redirect(url_for(VERIFY_2FA_URL))
    else:
        if not current_user.is_two_factor_authentication_enabled:
            flash(
                "You have not enabled 2-Factor Authentication. Please enable it first.", "info")
        return render_template("accounts/verify-2fa.html", form=form)


def _get_serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])


@accounts_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    # Allow both authenticated and unauthenticated users to request reset by username
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user:
            flash("If the username exists, a reset link will be shown below.", "info")
            return render_template("accounts/forgot-password.html", form=form)
        # Generate a single-use nonce
        user.password_reset_nonce = str(uuid.uuid4())
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Unable to generate reset link. Please try again.", "danger")
            return render_template("accounts/forgot-password.html", form=form)
        # Create a signed token with the user id and nonce
        s = _get_serializer()
        token = s.dumps({"uid": user.id, "nonce": user.password_reset_nonce})
        reset_link = url_for(RESET_PASSWORD_URL, token=token, _external=True)
        # In a real app, email this link. Here we display it for demo.
        flash("Copy the reset link below to reset your password.", "success")
        return render_template("accounts/forgot-password.html", form=form, reset_link=reset_link)
    return render_template("accounts/forgot-password.html", form=form)


@accounts_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    form = ResetPasswordForm()
    s = _get_serializer()
    try:
        data = s.loads(token, max_age=3600)  # token valid for 1 hour
    except SignatureExpired:
        flash("Reset link expired. Please request a new one.", "danger")
        return redirect(url_for(FORGOT_PASSWORD_URL))
    except BadSignature:
        flash("Invalid reset link.", "danger")
        return redirect(url_for(FORGOT_PASSWORD_URL))

    user = User.query.get(data.get("uid"))
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for(FORGOT_PASSWORD_URL))
    # Enforce single-use by matching nonce
    token_nonce = data.get("nonce")
    if not token_nonce or token_nonce != user.password_reset_nonce:
        flash("Reset link already used or invalid.", "danger")
        return redirect(url_for(FORGOT_PASSWORD_URL))

    if form.validate_on_submit():
        try:
            user.password = bcrypt.generate_password_hash(form.password.data)
            # Clear nonce so token cannot be reused
            user.password_reset_nonce = None
            db.session.commit()
            flash("Password has been reset. Please login.", "success")
            return redirect(url_for("accounts.login"))
        except Exception:
            db.session.rollback()
            flash("Failed to reset password. Please try again.", "danger")

    return render_template("accounts/reset-password.html", form=form)
