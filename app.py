from flask import Flask, request, render_template, redirect, url_for
import mains

app = Flask(__name__)

def read_credentials(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
        
    credentials = []
    current_user = {}
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            if current_user:
                credentials.append(current_user)
                current_user = {}
            current_user['name'] = line[2:]
        elif line.startswith('Mail:'):
            current_user['mail'] = line[6:]
        elif line.startswith('password:') or line.startswith('Password:'):
            current_user['password'] = line.split(':')[1].strip()
    
    if current_user:
        credentials.append(current_user)
    
    return credentials

def add_credentials_to_file(name, email, password):
    credentials = read_credentials('names.txt')
    if any(cred['mail'] == email for cred in credentials):
        print(f"Credentials for {email} already exist. Skipping addition.")
        return
    
    with open('names.txt', 'a') as file:
        file.write(f"# {name}\nMail: {email}\nPassword: {password}\n")
        print(f"Credentials for {email} added to file.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    add_credentials_to_file(name, email, password)
    
    # Call the function from the script with the username
    mains.run_script(name.lower())
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)