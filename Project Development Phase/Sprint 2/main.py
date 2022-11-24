import numpy as np
import os
from keras.models import load_model
from keras.preprocessing import image
from keras.applications.inception_v3 import preprocess_input
from cloudant.client import Cloudant
from keras.utils import img_to_array
import tensorflow as tf
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)

client = Cloudant.iam('513b10f8-8706-4471-b8c9-061547d5575b-bluemix', 'PyIQ2oP39O86Qy7gRwY6QHvmrc22VFI3l89FSshD8nFs',
                      connect=True)
my_database = client['ibmdiabetic']
app.secret_key = "SECRET_KEY"
model = load_model(r"diabeticretinopathy.h5")

image_folder = os.path.join('static', 'images')
app.config['UPLOAD_FOLDER'] = image_folder

@app.route('/')
def index():
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'drimage.jpg')
    return render_template('index.html', image=full_filename)

@app.route('/index')
def home():
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'drimage.jpg')
    return render_template('index.html', image=full_filename)


@app.route('/register')
def register():
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'registerimg.jpg')
    return render_template('register.html', image=full_filename)


@app.route('/afterreg', methods=['POST', 'GET'])
def afterreg():
    x = [x for x in request.form.values()]
    data = {
        '_id': x[2],
        'name': x[0],
        'pwd': x[4],
        'email': x[1],
        'location': x[3],
        'securityquestion': x[5],
        'logintype': x[6]
    }
    query = {'_id': {'$eq': data['_id']}}
    docs = my_database.get_query_result(query)
    if (len(docs.all()) == 0):
        url = my_database.create_document(data)
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'loginimg.jpg')
        return render_template('login.html', predict="Registration successfull please login using your credentials",
                               image=full_filename)
    else:
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'registerimg.jpg')
        return render_template('register.html', pred="You are already a member login using your credentials",
                               image=full_filename)

@app.route('/login')
def login():
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'loginimg.jpg')
    return render_template('login.html', image=full_filename)


@app.route('/afterlogin', methods=['POST', 'GET'])
def afterlogin():
    user = request.form['PID']
    session['pn'] = user
    passw = request.form['pwd']
    lgnas = request.form['loginas']

    query = {'_id': {'$eq': user}}
    docs = my_database.get_query_result(query)

    if (len(docs.all()) == 0):
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'loginimg.jpg')
        return render_template('login.html', predict="id not found", image=full_filename)
    else:
        if ((user == docs[0][0]['_id'] and passw == docs[0][0]['pwd'] and lgnas == docs[0][0]['logintype'])):
            if (docs[0][0]['logintype'] == 'user'):
                full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'retina.jpg')
                full_filename1 = os.path.join(app.config['UPLOAD_FOLDER'], 'image6.png')
                return render_template('prediction.html', image=full_filename, image2=full_filename1)
            if (docs[0][0]['logintype'] == 'admin'):
                full_filename2 = os.path.join(app.config['UPLOAD_FOLDER'], 'adminimg.png')
                return render_template('admin.html', image=full_filename2)
        if (lgnas != docs[0][0]['logintype']):
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'loginimg.jpg')
            return render_template('login.html', image=full_filename, predict="Incorrect Logintype")
        if (passw != docs[0][0]['pwd']):
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'loginimg.jpg')
            return render_template('login.html', image=full_filename, predict="Incorrect password")



@app.route('/prediction')
def prediction():
    full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'retina.jpg')
    full_filename1 = os.path.join(app.config['UPLOAD_FOLDER'], 'image6.png')
    return render_template('prediction.html', image=full_filename, image2=full_filename1)


@app.route('/afterpred', methods=["GET", "POST"])
def aftepred():
    if request.method == "POST":
        full_filename2 = os.path.join(app.config['UPLOAD_FOLDER'], 'retina.jpg')
        full_filename1 = os.path.join(app.config['UPLOAD_FOLDER'], 'image6.png')
        f = request.files['pfile']
        filepath = os.path.join('static', 'uploads', f.filename)
        f.save(filepath)
        img = tf.keras.utils.load_img(filepath, target_size=(64, 64))
        x = tf.keras.utils.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        img_data = preprocess_input(x)
        prediction = np.argmax(model.predict(img_data), axis=1)
        index = ["No DR", "Mild DR", "Moderate DR", "Severe DR", "Proliferate DR"]
        result = str(index[prediction[0]])
        return render_template('prediction.html', prediction=result, image=full_filename2, image2=full_filename1)
    else:
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'loginimg.jpg')
        return render_template('login.html', pred="Please login using your credentials", image=full_filename)




@app.route('/admin')
def admin():
    full_filename2 = os.path.join(app.config['UPLOAD_FOLDER'], 'adminimg.png')
    return render_template('admin.html', image=full_filename2)




@app.route('/logout')
def logout():
    session.pop('pn', None)
    return render_template('logout.html' )


if __name__ == "__main__":
    app.run(debug=False)

