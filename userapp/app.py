from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from proxmox import getISONetwork, createVM, deleteVM
from resources import getResources, getAllUserVM
from database import getUser, addUser
from azureVM import triggerPipeline
from werkzeug.security import check_password_hash
import json
import urllib3
from dotenv import load_dotenv
import os
from variables import generateTfvars


load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv("SECRET_KEY")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = getUser(username)

        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    errors = []
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form.get('userType')
        
        if not user_type:
            errors.append(f"Choice account type")
            return render_template('registration.html', errors=errors)

        existing_user = getUser(username)
        if existing_user:
            errors.append(f"This account name exists in database")
            return render_template('registration.html', errors=errors)

        addUser(username, password, user_type)
        return redirect(url_for('login'))
    return render_template('registration.html', errors=errors)


@app.route('/home')
def home():
    username = session['username']
    if 'username' not in session:
        return redirect(url_for('login'))
    userVM = getAllUserVM(username)
    resources = getResources()
    data = getISONetwork()
    return render_template('home.html', username=username, resources=resources, userVM=userVM, data=data)
 
@app.route('/create_vm', methods=['POST'])
def create_vm():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    userVM = getAllUserVM(username)
    resources = getResources()
    data = getISONetwork() 

    vmid = int(request.form['vmid'])
    vmname = request.form['vmname']
    memory = int(request.form['memory'])  
    cores = int(request.form['cores'])
    disk = int(request.form['disk']) 
    iso = request.form['iso']
    network = request.form['network']


    if memory > resources['freeRam'] or cores > resources['freeCPU'] or disk > resources['freeDisk']:
        try:
            generateTfvars(vmid, username, vmname, memory, cores, disk) 
            status, result = triggerPipeline()
            if status == 200 or status == 201:
                success = f"Brak zasobów w Proxmox — tworzę maszynę w Azure (pipeline ID: {result['id']})"
                return render_template('home.html', username=username, resources=resources, userVM=userVM, data=data, success=success)
            else:
                error = result.get("message", "Nie udało się uruchomić pipeline DevOps")
                return render_template('home.html', username=username, resources=resources, errors=[error], userVM=userVM, data=data)
        except Exception as e:
            return render_template('home.html', username=username, resources=resources, errors=[str(e)], userVM=userVM, data=data)
    try:
        result = createVM(vmid, vmname, memory, cores, disk, iso, network)
        if "error" in result:
            return render_template('home.html', username=username, resources=resources, errors=[result["error"]], userVM=userVM, data=data)
        return redirect(url_for('home')) 
    except Exception as e:
        return render_template('home.html', username=username, resources=resources, errors=[str(e)], userVM=userVM, data=data)


@app.route('/delete_vm', methods=['POST'])
def delete_vm():
    data = request.json
    vmid = data.get("vmid")

    if not vmid:
        return jsonify({"error": "Missing VM ID"}), 400
    try:
        result = deleteVM(vmid)
        if "error" in result:
            return jsonify({"error": result["error"]}), 500
        return jsonify({"success": f"VM {vmid} deleted successfully"})
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/getResource')
def getRes():
    resource = getResources()
    jsonData = json.dumps(resource)
    return Response(jsonData, mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True)
