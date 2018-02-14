import os
os.system("pip install flask")
os.system("cd flask")
os.system("pip install --editable disaggregation")
os.system("cd disaggregation")
os.system("export FLASK_APP=disaggregation.py")
os.system("flask initdb")
os.system("flask run --host=0.0.0.0")
