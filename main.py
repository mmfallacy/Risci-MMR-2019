import os,sys,json, datetime
from flask import Flask,render_template,request,session,send_from_directory

################################################
SESSION_SECRET_KEY = '72334c6965fa102866da48ae'
################################################

app = Flask(__name__)
app.secret_key = SESSION_SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] =  datetime.timedelta(days=3)
CURRENTDIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)

def isRegistered():
    return 'u-name' in session


with open(os.path.join(CURRENTDIR,"config","contestants.json"),"r") as CONTESTANT_CONFIG_FILE:
    CONTESTANT_LIST = json.load(CONTESTANT_CONFIG_FILE)
    CONTESTANT_LIST.insert(0,None)
with open(os.path.join(CURRENTDIR,"config","config.json"),"r") as CONFIG_FILE:
    _temp = json.load(CONFIG_FILE)
    SERVER_PORT=_temp["PORT"]
    DEBUG_MODE=_temp["DEBUG"]
    MMR_DATE = _temp["DATE"]

    
TOTAL_CONTESTANT_NUM =len(CONTESTANT_LIST)-1
TEMPLATE_404 = "404"
TEMPLATE_403 = "403"

CURRENT_CONTESTANT_NUMBER =1
CURRENT_USERNAME_LIST = [i for i in os.listdir(os.path.join(CURRENTDIR,"data"))]
THEME_LIST = ["thematic","casual","evening"]
PALETTE=["red","blue","green","#8EE4AF"]

# INDEX.HTML
@app.route("/")
def index():
    if isRegistered():
        return render_template("index.j2", bgColor=PALETTE[3],mmrdate=MMR_DATE, contestantNum = TOTAL_CONTESTANT_NUM)  
    else:
        return render_template("login.j2", error=" ")

# ICON
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(CURRENTDIR, 'static','images'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')

# LOGIN VALIDATION
@app.route("/login-validate",methods=['GET','POST'])
def login_validate():
    if request.method == "POST":
        _username = request.form['login-username']
        if _username in CURRENT_USERNAME_LIST:
            return render_template("login.j2", error="Username taken!")
        else:
            CURRENT_USERNAME_LIST.append(_username)
            session.permanent=True
            session['u-name'] = _username
            os.mkdir(os.path.join(CURRENTDIR,"data",_username))
            for theme in ['thematic','casual','evening']:
                os.mkdir(os.path.join(CURRENTDIR,"data",_username,theme))
            return render_template("login-validate.j2",username=_username)
    else:
        if isRegistered():
            return render_template("login-validate.j2",username=session['u-name'])
        else:
            return TEMPLATE_403


# THEME PAGES
@app.route("/<theme>")
def theme_route(theme):
    if theme in THEME_LIST and isRegistered():
        return render_template("theme-page.j2", bgColor=PALETTE[THEME_LIST.index(theme)],mmrdate=MMR_DATE,contestantNum = TOTAL_CONTESTANT_NUM,theme=theme)
    else:
        return TEMPLATE_403


# CONTESTANT PAGES
@app.route("/<theme>/<int:contestantnum>/")
def theme_route_contestant(theme,contestantnum):
    if theme in THEME_LIST and contestantnum <= TOTAL_CONTESTANT_NUM and contestantnum > 0:
        if isRegistered():
            global CURRENT_CONTESTANT_NUMBER
            CURRENT_CONTESTANT_NUMBER = contestantnum
            _path = os.path.join(CURRENTDIR,"data",session["u-name"],theme,str(contestantnum)+".json")
            if(os.path.isfile(_path)):
                CONTESTANT_SCORES = open(_path,"r")
                PREVIOUS_SCORES= json.load(CONTESTANT_SCORES)
            else:
                PREVIOUS_SCORES = "false"
            return render_template("contestant-page.j2",previousScores=PREVIOUS_SCORES, contestantNum = TOTAL_CONTESTANT_NUM,theme=theme,contestant=CONTESTANT_LIST[contestantnum], contestantnum=str(contestantnum))  
        else:
            return TEMPLATE_403
    else:
        return TEMPLATE_404

# AJAX HANDLER FOR SCORE UPDATES
@app.route("/<theme>/updateScores",methods=["GET","POST"])
def saveJSON(theme):
    if isRegistered() and request.method=="POST":
        _formdata = request.form
        _username = session["u-name"]
        with open(os.path.join(CURRENTDIR,"data",_username,theme,str(CURRENT_CONTESTANT_NUMBER)+".json"),'w+') as f:
            json.dump(_formdata, f, sort_keys=True, ensure_ascii=False, indent=4) 
        return "DONE"   
    else:
        return TEMPLATE_403


@app.errorhandler(404)
def page_not_found(e):
    return TEMPLATE_404

if DEBUG_MODE:
    import shutil
    @app.route("/print")
    def print_sessions():
        _temp_string = ""
        print(session)
        return "printed sessions<br> CURRENT USERS:<br>" +"<br>".join(CURRENT_USERNAME_LIST)
    @app.route("/release")
    def release():
        try:
            _username = session["u-name"]
            session.pop("u-name",None)
            print(CURRENT_USERNAME_LIST)
            if _username in CURRENT_USERNAME_LIST:
                CURRENT_USERNAME_LIST.remove(_username)
            return "released sessions"
        except Exception as e:
            print("ERROR")
            print(e)
            return "failed releasing sessions: ERROR:" + str(e)
    @app.route("/cleardata")
    def cleardata():
        shutil.rmtree(os.path.join(CURRENTDIR,"data"))
        os.mkdir(os.path.join(CURRENTDIR,"data"))   
        CURRENT_USERNAME_LIST.clear()
        return "cleared data"
if __name__=="__main__":
    app.run("0.0.0.0",SERVER_PORT, debug=DEBUG_MODE)