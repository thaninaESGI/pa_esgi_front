# Utiliser une image de base python
FROM python:3.10-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de requirements dans le répertoire de travail
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier tous les fichiers du projet dans le répertoire de travail
COPY . .

# Exposer le port utilisé par Streamlit
EXPOSE 8080

# Définir la commande pour exécuter Streamlit
CMD ["streamlit", "run", "your_streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
