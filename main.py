from flask import Flask, render_template, send_file, request, redirect, flash, session
from flask_session import Session
from pathlib import Path
import json
import textfileparser
from os import rename

app = Flask(__name__)                                          #make app object
app.secret_key = "9ef8yweoifh4itug4t"

#user session manager config
app.config["SESSION_PERMANENT"] = False                        # Sessions expire when the browser is closed
app.config["SESSION_TYPE"] = "filesystem"                      # Store session data in files
Session(app)                                                   #initialize session manager

#user data load
user_data = {}                                                 #dictionary to hold user data
with open("system/userdata.json", "r", encoding="utf-8") as file: #open the file
    user_data = json.load(file)                                #read le data
print('user data loaded: ', user_data)                         #debug print

#dir data load
directory_data = {}                                                 #dictionary to hold data
def reload_dir_data():
    global directory_data
    with open("system/filedata.json", "r", encoding="utf-8") as file: #open the file
        file_data = json.load(file)                                #read le data
    with open("system/folderdata.json", "r", encoding="utf-8") as file: #open the file
        folder_data = json.load(file)                                #read le data
    directory_data = folder_data | file_data
    print('file data loaded: ', file_data)                         #debug print
reload_dir_data()

def get_current_security_level():
    return user_data.get(session.get("name", ""), {}).get("security_level", 0)

def can_access_path(name, action:str, name_includes_root:bool=False):
    path = (DATA_DIR / name).as_posix()
    if name_includes_root:
        path = name.as_posix()
    file_level = directory_data.get(str(path), {}).get(action, 0)
    parent_level = directory_data.get(str(Path(path).parent.as_posix()), {}).get(action, 0)
    print('action: ', action, 'dir: ', path, ' file level: ', file_level, 'parent', str(Path(path).parent), 'parent level', parent_level, ' user level: ', get_current_security_level())
    return get_current_security_level() >= max(file_level, parent_level) 

DATA_DIR = Path("data")                                        #base directory for files

@app.route("/getfile/<path:name>")                             #request that simply sends the raw file
def getfile(name):
    if can_access_path(name, "access"):
        path = DATA_DIR / name
        return send_file(path)
    else:
        flash('You do not have clearance to access this file.')
        return redirect('/')

@app.route("/")                                                #user is at homepage
def home():
    return render_template("homepage.html",
        user=session.get('name', None),
        level=get_current_security_level()
        )                                                      #render and show homepage.html

@app.route("/files/")                                          #user is at files page
def index():
    filenames = list(DATA_DIR.iterdir())                           #get directories in data folder
    file_dict: dict = {}
    for filename in filenames:
        if can_access_path(filename, "access", True):# or get_current_security_level() > 0:
            if filename.is_dir():
                file_dict[filename] = "📁"
            else:
                if filename.suffix in [".txt", ".md"]:
                    file_dict[filename] = "📄"
                elif filename.suffix in [".png", ".svg", ".jpeg"]:
                    file_dict[filename] = "🖼️"
                elif filename.suffix in [".ogg", ".mp4", ".WebM"]:
                    file_dict[filename] = "🎥"
                elif filename.suffix in [".pdf"]:
                    file_dict[filename] = "📑"
                else:
                    file_dict[filename] = "❔"
            if not can_access_path(filename, "access", True):
                file_dict[filename] += "❌"
    return render_template("file_browser.html",
        files=file_dict,
        current_path='',
        path_parts=[],
        user=session.get('name', None),
        level=get_current_security_level()
        )                                                      #render file viewer html with base file directories

@app.route("/files/<path:name>")                               #when user as at some path in files (argue the path as 'name')
def files(name):
    path = DATA_DIR / name                                     #get the file path within the data folder

    if (not path.is_dir()) and (not path.is_file()):
            return "Not found", 404                                #if file not found, show error
    
    if can_access_path(name, "access"):
        if path.is_dir():                                          #if that path points to a folder
            filenames = list(path.iterdir())                       #get the directories in that folder
            file_dict: dict = {}
            for filename in filenames:
                if can_access_path(filename, "access", True):# or get_current_security_level() > 0:
                    if filename.is_dir():
                        file_dict[filename] = "📁"
                    else:
                        if filename.suffix in [".txt", ".md"]:
                            file_dict[filename] = "📄"
                        elif filename.suffix in [".png", ".svg", ".jpeg"]:
                            file_dict[filename] = "🖼️"
                        elif filename.suffix in [".ogg", ".mp4", ".WebM"]:
                            file_dict[filename] = "🎥"
                        elif filename.suffix in [".pdf"]:
                            file_dict[filename] = "📑"
                        else:
                            file_dict[filename] = "❔"
                    if not can_access_path(filename, "access", True):
                        file_dict[filename] += "❌"
            return render_template("file_browser.html",
                files=file_dict,
                current_path=name,
                path_parts=str(Path(name).as_posix()).split("/"),
                user=session.get('name', None),
                level=get_current_security_level()
            )                                                    #render and show them
            
        if path.is_file():                                       #if that path is a file
            if path.suffix in [".txt", ".md"]:                   #if text file
                content = path.read_text()                       #get the text
                content = textfileparser.parse_file(content, get_current_security_level())     #parse formatting
                print(str(Path(name).parent))
                return render_template(
                    "text_file.html",
                    filename=path.name,
                    content=content,
                    name=name,
                    parent_path = str(Path(name).parent),
                    user=session.get('name', None),
                    level=get_current_security_level()
                )                                                 #show it
            elif path.suffix in [".mp4"]:
                return render_template(                               
                    "video_viewer.html",
                    filename=path.name,
                    name=name,
                    parent_path = str(Path(name).parent),
                    user=session.get('name', None),
                    level=get_current_security_level()
                )
            elif path.suffix in [".pdf"]:
                return render_template(                               
                    "pdf_viewer.html",
                    filename=path.name,
                    name=name,
                    parent_path = str(Path(name).parent),
                    user=session.get('name', None),
                    level=get_current_security_level()
                )
            elif path.suffix in [".png", ".jpeg", ".svg"]:
                return render_template(                               
                    "image_viewer.html",
                    filename=path.name,
                    name=name,
                    parent_path = str(Path(name).parent),
                    user=session.get('name', None),
                    level=get_current_security_level()
                )

        return send_file(path)                                 #if the file type isn't recognized, just download it

    else:                                                      #if the user is not allowed to access the path
        flash('You do not have clearance to access this file.')
        return redirect('/files/')
        #return redirect(str(Path(name).parent))

@app.route("/upload", methods=["POST"])                        #user submits upload file form
def upload():
    file = request.files["file"]
    current_path = request.form["current_path"]                #get the file and path
    if can_access_path(current_path, "upload"):
        if file:
            directory = (DATA_DIR / current_path).resolve()
            destination = Path(str(directory) + '/' + str(file.filename)).resolve()    #get absolute target directory and destination filename

            if not directory.is_relative_to(DATA_DIR.resolve()):   #if target dir not in data folder
                return "Invalid directory", 400

            if not destination.is_relative_to(DATA_DIR.resolve()): #if target destingation not in data folder
                return "Invalid filename", 400

            if destination.exists():                               #if target file name already exists
                flash("A file with that name already exists.")
                redirect("/files/" + current_path)

            file.save(destination)
        else:
            flash("Please select a file to upload")
    else:
        flash("You do not have clearance to upload files here.")
    
    return redirect("/files/" + current_path)                  #reload

@app.route("/edit/<path:name>", methods=["GET", "POST"])       #user in edit page for a file (uses both GEt and POST commands)
def edit_file(name):
    path = DATA_DIR / name
    
    if not path.is_file():                                     #if that file does not exist
        return "Not found", 404

    if path.suffix not in [".txt", ".md"]:                     #if that not a text file
        return "This file type isn't editable.", 400

    if can_access_path(name, "edit"):
        if request.method == "POST":                               #if the page requested to POST the data
            content = request.form["content"]                      #get the form's content
            print(repr(content))
            path.write_text(content, newline="\n")                 #write it to file

            return redirect("/files/" + name)                      #go back to the file's page (exit)

        content = path.read_text()                                 #else if request was GET
                                                                #get the text (without parsing, to edit the raw)
        return render_template(                                    #show the file's edit page
            "edit_file.html",
            filename=path.name,
            name=name,
            content=content,
            current_path=name,
            user=session.get('name', None),
            level=get_current_security_level()
        )
    else:
        flash('You do not have clearance to edit this file.')
        return redirect('/files/' + str(name))

@app.route("/newfile", methods=["POST"])                       #user submits create a file form (presses the button)
def newfile():
    current_path = request.form["current_path"]
    if can_access_path(current_path, "add"):
        path = DATA_DIR / current_path / "new_file.txt"            #get path
        print('new file at ', path)
        try:
            with open(path, "x", encoding="utf-8") as file:
                file.write("New File")                             #create file
        except FileExistsError:
            flash('A New File already exists. Rename or delete it first.')
        return redirect("/files/" + current_path)                  #reload
    else:
        flash('You do not have clearance to create a new file here.')
        return redirect("/files/" + current_path)

@app.route("/rename", methods=["POST"])                        #user submits rename current file form
def renamefile():
    current_path = str(request.form["current_path"])
    new_name = request.form["new name"]
    sanitized_name = new_name.replace('/', '-').replace(' ', '_')

    old_path = str(DATA_DIR) + '/' + current_path
    new_path = Path(str(Path(old_path).parent) + '/' + sanitized_name).as_posix()

    print('rename', current_path, ' to ', new_path)
    try:
        rename(old_path, new_path)
        print("File renamed successfully!")
    except FileNotFoundError:
        flash(f"Error: The file '{old_path}' does not exist.")
    except FileExistsError:
        flash(f"Error: A file named '{new_path}' already exists.")

    return redirect("/edit/" + Path(str(Path(current_path).parent) + '/' + new_name).as_posix())

@app.route("/login", methods=['GET', 'POST'])                  #user on login page / submits login form
def login():
    if request.method == "POST":                               #if request was form submission
        username = request.form.get("username", '').strip()    #get entered username
        password = request.form.get("password", '').strip()    #get entered password
        if user_data.get(username, {}).get('password', '') == password: #check if name and password match a user on file
            session["name"] = request.form.get("username")     #add session
            print(session["name"], ' logged in')               #debug print
            return redirect("/")                               #redirect to home
        else:                                                  #if name and pass do not match any user
            print('login attempt: ' + username + '-' + password) #debug print
            flash('login data does not match any user on file')  #warning message
            return redirect('/login')                          #reload page
    
    return render_template("login.html",                       #if request was GET
        user=session.get('name', None)        
        )                                                      #render and return login page

@app.route("/logout")                                          #user requests logout
def logout():
    session["name"] = None                                     #remove session
    return redirect("/")                                       #redirect to home page

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=1348)                                      #run le app