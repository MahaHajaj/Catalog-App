# Catalog Application
The second project in Udacity's full stack web development nanodegree program
The aim of the project is building an list of items within a variety of categories .

## what Application does:
- Listing categories names
- List the items for each categories
- Show the description of the item
- Add a new item
- Edit and delete item

**Prerequisites :**
- Flask
- Python
- Vagrant
- VirtualBox

**Skills used for this project :**
- Python
- Flask
- HTML
- CSS
- Bootstrap
- SQLAchemy
- Google oauth2 Client ID

**Installing :**
1. Install [Vagrant](https://www.vagrantup.com/downloads.html) and [VirtualBox](https://www.virtualbox.org/wiki/Downloads).
2. Download or fork and clone from github [fullstack-nandegree-vm](https://github.com/udacity/fullstack-nanodegree-vm) repository.
3. Install Flask using ```pip install Flask```.

**Running :**
1. Start VM using ```vagrant up```.
2. Log in to VM using ```vagrant ssh```.
3. Change directory to ```/vagrant/catalog```.
4. Setup application database ```python database_setup.py```.
5. Insert data ```python3 lotsofitem.py```.
6. Run the python file using ```python application.py```.
7. Access the application locally using http://localhost:8000 .
