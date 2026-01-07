import os
from flask import Flask, render_template, request, url_for
import csv
from  charts import filmsByGenreChart,  filmsByRatingChart


# Create an Object app
app = Flask(__name__)


#fileName = os.path.join("static", "files", "films.csv")
fileName= "./static/files/films.csv"


def loadDataFilms():
    """
    Retorna os dados dos filmes e o header (nomes dos atributos)
    """
    with open(fileName, newline='', encoding='utf-8') as csvfile:
        filmsReader = csv.reader(csvfile, delimiter=',', quotechar='"')
        header = next(filmsReader)  # Skip header
        filmsData = list(filmsReader)   
        filmsData = filmsData[:50]  # Load only first 50 films

    # Cleaning de data - remove films with missing Year or Rating
    filmsDelete = []
    for film in filmsData:
        if  film[2] == "" : filmsDelete.append(film)
        if  film[6] == "" : filmsDelete.append(film)
    for film in filmsDelete:
        if film in filmsData:
            filmsData.remove(film)

    return filmsData, header  



# ----- Middleware Example -----    
@app.before_request
def before():
    global filmsData, header
    # Load data once before handling any request
    filmsData, header = loadDataFilms()
    global filmsFilter
    filmsFilter = filmsData     # Initialize filtered data with all films 
    
    global defaultOption    
    defaultOption = ""
    




def dataTableHTML(filmsData):
    """
    Retorna os dados dos filmes em formato HTML (tabela)
    """
   
    tableHTML= "<table><tr><th width='50%'>Movie Name</th> <th width='15%'>Year</th><th width='30%'>Film Genre</th><th width='15%'>Rating</th></tr>"
    tableHTML += "\n"   
    for film in filmsData:  
        tableHTML += "<tr>\n"
        tableHTML += f"  <td>{film[1][:35]}</td>\n"
        tableHTML += f"  <td>{film[2]}</td>\n"
        tableHTML += f"  <td>{film[5]}</td>\n"
        tableHTML += f"  <td>{film[6]}</td>\n"
        tableHTML += "</tr>\n"
    tableHTML += "</table>\n"
    return tableHTML



def createOptionsHTML(defaultOption):
    # CREATE OPTIONS FOR GENRE SELECT   
    dataOptionsHTML =   ""
    genreIndex = 5  # Index of Genre in data
    uniqueGenres = set()
    for film in filmsData:
        genres = film[genreIndex].split(", ")  # Some films have multiple genres separated by comma
        for genre in genres:
            if genre not in uniqueGenres:
                uniqueGenres.add(genre)     
    uniqueGenres = sorted(uniqueGenres)  # Sort genres alphabetically

    dataOptionsHTML += '<option value="">-- All Genres --</option>\n'
    for genre in uniqueGenres:
        if genre == defaultOption:
            dataOptionsHTML += f'<option value="{genre}" selected>{genre}</option>\n'
        else:       
            dataOptionsHTML += f'<option value="{genre}">{genre}</option>\n'        
    return dataOptionsHTML



#------------------------------Paths / Routes -------------------------------
"""
Rota para a página inicial - index
"""
@app.route("/", methods=["GET", "POST"])
def index():

     
    global defaultOption
    dataOptionsHTML = createOptionsHTML(defaultOption) # OPTIONS FOR GENRE SELECT
    
    global filmsFilter     # Filtered data initialized in before_request (all films at first)
    tableHTML = dataTableHTML(filmsFilter)

    
    # FILTER BY GENRE    
    if request.method == "POST" :
        genreFilter = request.form['filmGenre']   # Genre selected in options

        if genreFilter != "":
            filmsFilter = [film for film in filmsData if genreFilter in film[5] ]
        else:
            filmsFilter = filmsData

        # SORT BY NAME
        if request.method == "POST" and "btnSort" in request.form:
            filmsFilter = sorted(filmsFilter, key=lambda x: x[1])
        
        if request.method == "POST" and "btnRating" in request.form:
            filmsFilter = sorted(filmsFilter, key=lambda x: float(x[6]), reverse=True)

        tableHTML = dataTableHTML(filmsFilter)  # HTML table with filtered data
        defaultOption = genreFilter
        dataOptionsHTML = createOptionsHTML(defaultOption) # OPTIONS FOR GENRE SELECT

    
    return render_template("index.html", sltOption= dataOptionsHTML, filmsTable=tableHTML)




""" 
 rota para adicionar filmes - apenas renderiza o template
""" 
@app.route("/FilmsCatalog", methods=["GET"])
def filmsCatalog():

    fileCovers = "./static/files/covers.csv"
    with open(fileCovers, newline='', encoding='utf-8') as csvfile:
        filmsReader = csv.reader(csvfile, delimiter=',', quotechar='"')
        header = next(filmsReader)  # Skip header
        filmsData = list(filmsReader)   

    catalogHTML = ""
    for film in filmsData:
        linkImage = url_for('static', filename='images/filmsCovers/' + film[0])
        
        catalogHTML += f"""
        <div class="card-group">
            <div class="card">
                <img src=\"{linkImage}\"  alt=\"Cover of {film[1]}\" class=\"card-img\" />
                <div class=\"card-body\">
                    <h5 class=\"card-title\">{film[1]}</h5>
                    <a class=\"btn btn-primary\" href=\"#\">Ver Mais</a>
                </div>
            </div>
        </div>
        """

    return render_template("filmsCatalog.html", catalog = catalogHTML)


 





""" 
 rota para autenticação do utilizador 
""" 

def guardarUserFicheiro(userName, password):

    filePath = "./static/files/users.bin"

    if not os.path.exists(filePath):
        with open(filePath, "wb") as fileUsers:
            pass  # Create the file if it does not exist

    with open(filePath, "ab") as fileUsers:
        userAccount = userName + "," + password + "\n"
        fileUsers.write(userAccount.encode('utf-32'))




@app.route("/Authentication", methods=["GET", "POST"])
def authentication():

    caracteresNaoAutorizados = "<>[]{}=+-_()/\\;:,\"'`~^"
    messageUser = ""
    if request.method == "POST" :
        userName = request.form['txtUsernameRegister']   # username from form
        password = request.form['txtPasswordRegister']   # password from form
        password2 = request.form['txtPasswordRegister2'] # confirm password from form
        if password != password2:
            messageUser = "Error: Passwords do not match!"
        else:
            for char in userName:
               if char in caracteresNaoAutorizados:
                   messageUser = "Error: Username contains invalid characters!"
               else:
                   # REGISTAR EM FICHEIRO (append mode)
                   guardarUserFicheiro(userName, password)
                   messageUser = f"User {userName} registered successfully!"

    return render_template("authentication.html", message = messageUser)




"""
rota para o dashboard - gráficos
"""
@app.route("/Dashboard",  methods=["GET", "POST"])
def dashboard():

    global filmsData, header
    chartPath1 = filmsByGenreChart(header, filmsData)
    chartPath2 = filmsByRatingChart(header, filmsData)

    return render_template("dashboard.html", imagePlot1=chartPath1, 
                                             imagePlot2=chartPath2,)



# Flask Constructor
if __name__ == "__main__":
    app.run(debug=True)
