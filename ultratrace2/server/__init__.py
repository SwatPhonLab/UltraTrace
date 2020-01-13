from flask import Flask


app = Flask(__name__)

# server config goes here
print(__name__)

from . import views
