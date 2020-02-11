from flask import Flask, send_file, make_response, render_template, request, redirect, url_for
import matplotlib.pyplot as plt
import os
import sqlite3
import io
import pandas as pd

app = Flask(__name__)

env = os.getenv("run_env", "dev")
if env == "dev":
    BASE_URL = "http://localhost:5000/"
elif env == "prod":
    BASE_URL = "https://budget-on-track.herokuapp.com/"

conn = sqlite3.connect("expenses.db")

all_data=[]

with sqlite3.connect("expenses.db") as conn:
	try:
		all_data = conn.execute( "SELECT * FROM Expenses;").fetchall()
	except:
		conn.execute("CREATE TABLE Expenses (ID INT PRIMARY KEY NOT NULL, DAY TEXT NOT NULL, DESC TEXT NOT NULL, AMT REAL NOT NULL);")
		all_data = conn.execute( "SELECT * FROM Expenses;").fetchall()

date,desc,amt=[i[1] for i in all_data],[i[2] for i in all_data],[i[3] for i in all_data]

@app.route('/track-budget')
def plot():
	global all_data
	bytes_obj = io.BytesIO()
	with sqlite3.connect("expenses.db") as conn:
		all_data=conn.execute( "SELECT * FROM Expenses;").fetchall()
	print(all_data)
	if len(all_data)==0:
		plt.figure()
		plt.xticks([])
		plt.yticks([])
		plt.text(.25, .5, "Add your first entry to see the graph")
	else:
		with sqlite3.connect("expenses.db") as conn:
			plt.figure()
			print([i[-1] for i in all_data])
			df = pd.DataFrame(data=conn.execute( "SELECT * FROM Expenses;").fetchall(),columns=['ID','Day','Vendor','Amount']) 
			expenses = df.Amount.groupby(df.Vendor).sum()
			exp_idx = ["{0}: ₹{1} - {2:1.2f} %".format(i,j,k) \
			for i,j,k in zip(expenses.index,expenses,100.*expenses/expenses.sum())]		
			patches=plt.pie([i[-1] for i in all_data],shadow=True,labeldistance=1.1)
			plt.legend(patches[0], exp_idx, loc='upper left', bbox_to_anchor=(0.7, 1.),
			    fontsize=8)
	
	plt.savefig(bytes_obj,format='png')
	bytes_obj.seek(0)
	return send_file(bytes_obj,attachment_filename='plot.png',
                        mimetype='image/png') 


@app.route('/reset')
def clear_db():
	with sqlite3.connect("expenses.db") as conn:
		conn.execute("DELETE FROM Expenses;")
	print("database cleared")
	return redirect(url_for('index'))


@app.route('/')
def index():
	bytes_obj = plot()	
	return render_template('index.html', base_url=BASE_URL)



@app.route('/', methods=['GET','POST'])
def pie_chart():
	global date, desc,amt
	
	if request.method=='POST':
		print(request.form['date'],request.form['desc'],request.form['amount'])
		
		date.append(request.form["date"])
		desc.append(request.form["desc"])
		amt.append(float(request.form["amount"]))
		with sqlite3.connect("expenses.db") as conn:
			last_id = len(conn.execute("SELECT * FROM Expenses;").fetchall())
			print(last_id)
			query="INSERT INTO Expenses(ID, DAY, DESC, AMT) VALUES"+\
			str((last_id+1, request.form['date'],request.form['desc'],float(request.form['amount'])))+";"
			print(query)			
			conn.execute(query)
			conn.commit()
		print(date,desc,amt)
		bytes_obj = plot()	
		return render_template('index.html', base_url=BASE_URL)


	

if __name__ =="__main__":
    if env == "dev":
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.run(debug=True)
    else:
        app.run(debug=False)

