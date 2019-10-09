pip install flask
cd flask
pip install --editable disaggregation
cd disaggregation
export FLASK_APP=disaggregation.py
flask initdb
flask run --host=0.0.0.0
