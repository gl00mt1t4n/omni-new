import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.raw_data import export_all_wallets

app = Flask(__name__)

@app.route("/")
def home():
    wallets = export_all_wallets()
    return render_template("dashboard.html", wallets=wallets)

if __name__ == "__main__":
    app.run(debug=True)
