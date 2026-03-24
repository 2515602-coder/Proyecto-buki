from flask import Flask, render_template, request, flash
from consolex import console
from dotenv import load_dotenv
import re
import pymysql
import os

import pymysql