import flask
from flask import Flask, render_template, request, url_for, redirect
from werkzeug.utils import secure_filename
from pdf_gui import generate_two_col
from SummaryPage import build_summary_page

app = Flask(__name__)

@app.route('/')
def home ():
    return redirect(url_for('upload'))

@app.route('/upload')
def upload ():
    return render_template('upload_page.html', uploader_address=url_for('file_uploader'))

@app.route('/uploader', methods=['GET', 'POST'])
def file_uploader ():
    if request.method == 'POST':
        f = request.files['file']
        sec_fname = secure_filename(f.filename)
        f.save(sec_fname)
        #return redirect(url_for('explorer', doc_id=sec_fname))
        return redirect(url_for('summary_page', doc_id=sec_fname))

@app.route('/summary/<string:doc_id>')
def summary_page (doc_id):
    return build_summary_page(doc_id, url_for('explorer', doc_id=doc_id, page_num=0))

@app.route('/explorer/<string:doc_id>/<int:page_num>')
def explorer (doc_id, page_num):
    return generate_two_col(doc_id, page_num)

if __name__== '__main__':
    app.run(debug=True, host='0.0.0.0')

