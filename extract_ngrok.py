import zipfile
import os

with zipfile.ZipFile('ngrok.zip', 'r') as zip_ref:
    zip_ref.extractall('.')

print("Ngrok extracted successfully")
