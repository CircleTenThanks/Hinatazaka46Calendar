import time
import pickle
import os
from tendo import singleton
import mojimoji
import re
import requests
from bs4 import BeautifulSoup
import datetime
from dateutil.relativedelta import relativedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.transport.requests import Request
"""
このモジュールは、他のモジュールで使用される依存関係をインポートするためのものです。
主に、外部ライブラリやPython標準ライブラリから必要なモジュールをインポートしています。
これにより、他のモジュールでのコードの記述が簡潔になり、再利用性が向上します。
"""
