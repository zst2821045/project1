#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
import datetime
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following uses the postgresql test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@104.196.183.105/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# Swap out the URI below with the URI for the database created in part 2
DATABASEURI = "postgresql://ya2366:m2ewk@104.196.175.120/postgres"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT movie_id, movie_name FROM movie")
  data = []
  line=1
  for result in cursor:
    line=result
    data.append([result['movie_id'],result['movie_name']])  # can also be accessed using result[0]
  cursor.close()
  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(movie_info = data)





  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("main.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/movieid/<movie_id>')
def display_movie(movie_id):
    cursor = g.conn.execute("SELECT * from movie WHERE movie.movie_id= %s", movie_id)
    result=cursor.fetchone()
    context= dict(items=result.items())
    context['attr']= result.keys()
    cursor.close()

    return render_template("display_movie.html", **context)

@app.route('/get_score',methods=['POST'])
def get_score():
  name=request.form['name']
  print name
  score=[]
  cursor = g.conn.execute("SELECT AVG(rate_score) FROM feedback,movie WHERE feedback.movie_id=movie.movie_id and movie.movie_name=%s",name)
  for result in cursor:
  	score.append(result)
  cursor.close()
  context=dict()
  context['scores']=score
  context['movie_name']=name

  return render_template("get_score.html", **context)

moviename= "1"

@app.route('/get_comment',methods=['POST'])
def get_comment():
  name=request.form['name']
  print name
  cursor = g.conn.execute("SELECT * FROM feedback JOIN movie ON feedback.movie_id=movie.movie_id WHERE movie.movie_name=%s",name)
  comment = []
  for result in cursor:
    comment.append(result['reviews'])  # can also be accessed using result[0]
  cursor.close()
  context=dict()
  context['review']=comment
  context['movie_name']=name
  moviename=name
  return render_template('get_comment.html',**context)

@app.route('/get_comment/add_comment',methods=['POST'])
def add_comment():
  username=request.form['username']
  comment = request.form['comment']
  rate = request.form['rate']
  time = datetime.datetime.now()
  cursor1=g.conn.execute("SELECT movie_id FROM movie WHERE movie_name= %s", moviename)
  movieid= cursor1.fetchone()['movie_id']
  cursor = g.conn.execute("INSERT INTO feedback(time, rate_score, review, account,movie_id) VALUES(%s,%s,%s,%s,%s)", time, rate,comment, username, movieid)
  cursor.close()
  cursor1.close()
  return redirect('get_comment.html')

@app.route('/director')
def director():
  cursor = g.conn.execute("SELECT staff.name FROM staff JOIN director ON director_id=staff_id")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()
  context=dict(data=names)
  return render_template("director.html",**context)
  
@app.route('/actor')
def actor():
  cursor = g.conn.execute("SELECT staff.name FROM staff JOIN actor ON actor_id=staff_id")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()
  context = dict(data = names)
  return render_template("director.html",**context)


# Example of adding new data to the database
@app.route('/director/add_director', methods=['POST'])
def add_director():
  name = request.form['name']
  id=request.form['id']
  print id,name
  g.conn.execute("INSERT INTO staff(staff_id, name) VALUES(%s,%s)",id,name);
  g.conn.execute("INSERT INTO director(director_id) VALUES(%s)",id);
  return redirect('/director')

@app.route('/actor/add_actor', methods=['POST'])
def add_actor():
  name = request.form['name']
  id=request.form['id']
  print id,name
  g.conn.execute("INSERT INTO staff(staff_id, name) VALUES(%s,%s)",id,name);
  g.conn.execute("INSERT INTO actor(actor_id) VALUES(%s)",id);
  return redirect('/actor')

@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
