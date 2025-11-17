from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/diabetes')
def diab():
    return render_template('diabetes.html')

@app.route('/heart')
def heart():
    return render_template('heart.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)