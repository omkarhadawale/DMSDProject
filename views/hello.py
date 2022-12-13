from flask import Blueprint, render_template, request
hello = Blueprint('hello', __name__, url_prefix='/')


@hello.route('/')
def index():
    return render_template("index.html")