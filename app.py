from flask import Flask, render_template_string, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.secret_key = 'ma_cle_secrete'

# "Base de données" simplifiée pour la démo
users = {}
tasks = {}

# Bloc CSS commun
base_css = """
<style>
  body {
    font-family: Arial, sans-serif;
    background-color: #f2f2f2;
    margin: 0;
    padding: 0;
  }
  .container {
    max-width: 600px;
    margin: 50px auto;
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }
  h1, h2, h3 {
    color: #333;
  }
  a {
    color: #0066cc;
    text-decoration: none;
  }
  a:hover {
    text-decoration: underline;
  }
  input[type="text"],
  input[type="password"] {
    width: 80%;
    padding: 8px;
    margin: 4px 0;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  button {
    background-color: #0066cc;
    color: white;
    padding: 10px 15px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  button:hover {
    background-color: #004d99;
  }
  .error {
    color: red;
  }

  /* Styles spécifiques pour la liste des tâches */
  .task-list {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .task-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #fafafa;
    margin-bottom: 10px;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .task-desc {
    flex: 1;
  }
  .task-actions a.button {
  display: inline-block;
  margin-right: 5px;
  padding: 6px 12px;
  background-color: #0066cc;
  color: white;
  border-radius: 4px;
  text-decoration: none;
  font-size: 0.9rem;
}

/* Edit button hover = red */
.task-actions a.edit-button:hover {
  background-color: yellow;
  color: black; 
}

/* Delete button hover = yellow */
.task-actions a.delete-button:hover {
  background-color: red;
  
}
</style>
"""

index_template = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Application SaaS</title>
    {base_css}
</head>
<body>
<div class="container">
    <h1>Bienvenue dans l'application SaaS</h1>
    <p>
        <a href="{{{{ url_for('login') }}}}">Se connecter</a> ou 
        <a href="{{{{ url_for('register') }}}}">S'inscrire</a>
    </p>
</div>
</body>
</html>
'''

login_template = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Connexion</title>
    {base_css}
</head>
<body>
<div class="container">
    <h1>Connexion</h1>
    {{% if error %}}
      <p class="error">{{{{ error }}}}</p>
    {{% endif %}}
    <form method="POST">
        <label for="username">Nom d'utilisateur :</label>
        <input type="text" name="username" id="username" required>
        <br><br>
        <label for="password">Mot de passe :</label>
        <input type="password" name="password" id="password" required>
        <br><br>
        <button type="submit">Se connecter</button>
    </form>
    <p>Pas de compte ? <a href="{{{{ url_for('register') }}}}">Inscrivez-vous ici</a>.</p>
</div>
</body>
</html>
'''

register_template = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Inscription</title>
    {base_css}
</head>
<body>
<div class="container">
    <h1>Inscription</h1>
    {{% if error %}}
      <p class="error">{{{{ error }}}}</p>
    {{% endif %}}
    <form method="POST">
        <label for="username">Nom d'utilisateur :</label>
        <input type="text" name="username" id="username" required>
        <br><br>
        <label for="password">Mot de passe :</label>
        <input type="password" name="password" id="password" required>
        <br><br>
        <button type="submit">S'inscrire</button>
    </form>
    <p>Déjà inscrit ? <a href="{{{{ url_for('login') }}}}">Connectez-vous ici</a>.</p>
</div>
</body>
</html>
'''

dashboard_template = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Tableau de bord</title>
    {base_css}
</head>
<body>
<div class="container">
    <h1>Bienvenue, {{{{ username }}}}!</h1>
    <p>Ceci est votre tableau de bord SaaS.</p>
    
    <h2>Vos tâches</h2>
    {{% if tasks %}}
    <ul class="task-list">
        {{% for task in tasks %}}
            <li class="task-item">
                <span class="task-desc">{{{{ task['description'] }}}}</span>
                <div class="task-actions">
                    <a class="button edit-button"  href="{{{{ url_for('edit_task', task_id=task['id']) }}}}">Modifier</a>
                    <a class="button delete-button" href="{{{{ url_for('delete_task', task_id=task['id']) }}}}">Supprimer</a>
                </div>
            </li>
        {{% endfor %}}
    </ul>
    {{% else %}}
    <p>Vous n'avez pas encore de tâches.</p>
    {{% endif %}}
    
    <h3>Ajouter une nouvelle tâche :</h3>
    <form method="POST" action="{{{{ url_for('dashboard') }}}}">
        <input type="text" name="new_task" placeholder="Entrez une nouvelle tâche" required>
        <button type="submit">Ajouter</button>
    </form>
    
    <p><a href="{{{{ url_for('logout') }}}}">Déconnexion</a></p>
</div>
</body>
</html>
'''

edit_template = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Modifier la tâche</title>
    {base_css}
</head>
<body>
<div class="container">
    <h1>Modifier la tâche</h1>
    <form method="POST">
        <input type="text" name="new_description" value="{{{{ description }}}}" required>
        <button type="submit">Enregistrer</button>
    </form>
    <p><a href="{{{{ url_for('dashboard') }}}}">Retour au tableau de bord</a></p>
</div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(index_template)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username not in users:
            error = "Nom d'utilisateur inconnu."
        elif not check_password_hash(users[username], password):
            error = "Mot de passe incorrect."
        else:
            session['username'] = username
            tasks.setdefault(username, [])
            return redirect(url_for('dashboard'))
    return render_template_string(login_template, error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            error = "Nom d'utilisateur déjà utilisé."
        else:
            users[username] = generate_password_hash(password)
            tasks[username] = []
            session['username'] = username
            return redirect(url_for('dashboard'))
    return render_template_string(register_template, error=error)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    if request.method == 'POST':
        new_task_desc = request.form.get('new_task')
        if new_task_desc:
            new_task = {'id': str(uuid.uuid4()), 'description': new_task_desc}
            tasks.setdefault(username, []).append(new_task)
        return redirect(url_for('dashboard'))
    user_tasks = tasks.get(username, [])
    return render_template_string(dashboard_template, username=username, tasks=user_tasks)

@app.route('/delete/<task_id>')
def delete_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    tasks[username] = [t for t in tasks.get(username, []) if t['id'] != task_id]
    return redirect(url_for('dashboard'))

@app.route('/edit/<task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user_tasks = tasks.get(username, [])
    task = next((t for t in user_tasks if t['id'] == task_id), None)
    if task is None:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        new_description = request.form.get('new_description')
        if new_description:
            task['description'] = new_description
        return redirect(url_for('dashboard'))
    return render_template_string(edit_template, description=task['description'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
