import flask
from flask import Flask, render_template, request, url_for, redirect, jsonify
import werkzeug
from werkzeug.utils import secure_filename
from checks import check_bitmapped_pages
import json

app = Flask(__name__)

def bad_request(message):
    response = jsonify({'message': message})
    response.status_code = 400
    return response

@app.route('/checks/all', methods=['POST'])
def all_checks ():
    print ("Received query")
    if request.method == 'POST':
        try:
            f = request.files['file'] 
            sec_fname = secure_filename(f.filename)
        except werkzeug.exceptions.BadRequestKeyError:
            return bad_request("File must be attached in (key: value) pair: ('file': *.pdf)")
        f.save(sec_fname)
        try:
            check_dict = {
                "bitmapped_images": check_bitmapped_pages(sec_fname)
            }
        except:
            return bad_request("Attached file is not a pdf")
        return check_dict # Automatically jsonifies it

if __name__== '__main__':
    app.run(debug=True, host='0.0.0.0')
