# views.py

from flask import  Flask, render_template, Response
from flask_basicauth import BasicAuth
from flask import redirect, url_for, request, flash
import pandas as pd
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import numbers
import string
import nltk
import json
import joblib
import io
import os
import random
from matplotlib import pyplot as plt
import numpy as np


from app import app

app.config['BASIC_AUTH_USERNAME'] = os.environ['SHAKEUSER']
app.config['BASIC_AUTH_PASSWORD'] = os.environ['SHAKEPASS']
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)

@app.route('/secret')
@basic_auth.required
def secret_view():
    return render_template('secret.html')

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
pipeline = joblib.load('pipeline.joblib')
NOS = pd.read_excel('NOS_database_table_of_contents.xls', sheet_name='phase1_table_of_contents')


def es_ngram_no_of_hits_query(es, ngram, collocation):
	que = { "from" : 0, "size" : 1,
			"_source" : {
			"includes" : [""]
			},
			"query": 
			{ 
				"multi_match" : 
				{ "query" : ngram, 
				"fields" : ["Text", "Title"], 
				"type" : "phrase", 
				"slop" : collocation 
				}
			}
		}

	res = es.search(index='test_index', body = que, request_timeout=1000)
	return res

def es_ngram_query(es, ngram, collocation, size=100):
	que = { "from" : 0, "size" : size,
			"_source" : {
			"includes" : ["TCP_ID"]
			},
			"query": 
			{ 
				"multi_match" : 
				{ "query" : ngram, 
				"fields" : ["Text", "Title"], 
				"type" : "phrase", 
				"slop" : collocation 
				}
			}, 
			"highlight":
			{
				"fields":
				{
					"Text": {},
					"Title": {}
				}
			}
		}

	res = es.search(index='test_index', body = que, request_timeout=600)
	return res

def es_query_author(es, low_year, high_year, author_arr, ngram, collocation, size, include_year_unknown, tcpid="None", timeout=600):

	low = -10000
	high = 10000
	quer = "should"
	if (not include_year_unknown):
		low = 10000
		high = -10000
		quer = "must"

	if len(author_arr) < 15:
	    length = len(author_arr)
	    for i in range(15-length):
	        author_arr.append("")
	        
	que = {"from" : 0, "size" : size,
	    "_source" : {
	    "includes" : ["TCP_ID"]
	    },
	    "query" : {
	        "bool": {
	            "must": [{
	                "bool" : {
	                    "must_not" : 
	                        { "match" : {"TCP_ID": tcpid} }
	                }}, { 
	                "bool": {
	                    quer : [
	                        {"range" :{"Year": {"gte": low_year, "lte": high_year}}},
	                        {"bool" : {"must_not":[{"range" : {"Year":{"gte":low, "lte":high}}}] }}
	            
	                    ]
	                }}, {
	                "bool": {
	                    "must" : 
	                    {
	                        "bool": {
	                            "should" :[
	                                {"match": {"Author" : author_arr[0]}},
	                                {"match": {"Author" : author_arr[1]}},
	                                {"match": {"Author" : author_arr[2]}},
	                                {"match": {"Author" : author_arr[3]}},
	                                {"match": {"Author" : author_arr[4]}},
	                                {"match": {"Author" : author_arr[5]}},
	                                {"match": {"Author" : author_arr[6]}},
	                                {"match": {"Author" : author_arr[7]}},
	                                {"match": {"Author" : author_arr[8]}},
	                                {"match": {"Author" : author_arr[9]}},
	                                {"match": {"Author" : author_arr[10]}},
	                                {"match": {"Author" : author_arr[11]}},
	                                {"match": {"Author" : author_arr[12]}},
	                                {"match": {"Author" : author_arr[13]}},
	                                {"match": {"Author" : author_arr[14]}}
	                            ]
	                        }
	                    }
	                    
	                }
	                
	            }], 
	            "filter":
	            {
	               "multi_match":
	                        {
	                            "query": ngram,
	                            "fields" : ["Text", "Title"], 
	                            "type" : "phrase", 
	                            "slop" : collocation 
	                        }
	                       }
	                }
	            },
	            "highlight":
	            {
	                "fields":
	                {
	                    "Text": {},
	                    "Title": {}
	                }
	            }
	        }
	res = es.search(index='test_index', body = que, request_timeout=timeout)
	return res

def es_query_no_author(es, low_year, high_year, ngram, collocation, size, include_year_unknown, tcpid="None", timeout=600):
        
	low = -10000
	high = 10000
	quer = "should"
	if (not include_year_unknown):
		low = 10000
		high = -10000
		quer = "must"

	que = {"from" : 0, "size" : size,
	    "_source" : {
	    "includes" : ["TCP_ID"]
	    },
	    "query" : {
	        "bool": {
	            "must": [{
	                "bool" : {
	                    "must_not" : 
	                        { "match" : {"TCP_ID": tcpid} }
	                }}, {
	                "bool": {
	                    quer : [
	                        {"range" :{"Year": {"gte": low_year, "lte": high_year}}},
	                        {"bool" : {"must_not":[{"range" : {"Year":{"gte":low, "lte":high}}}] }}
	            
	                    ]
	                }
	                
	            }], 
	            "filter":
	            {
	               "multi_match":
	                        {
	                            "query": ngram,
	                            "fields" : ["Text", "Title"], 
	                            "type" : "phrase", 
	                            "slop" : collocation 
	                        }
	                       }
	                }
	            },
	            "highlight":
	            {
	                "fields":
	                {
	                    "Text": {},
	                    "Title": {}
	                }
	            }
	        }
	res = es.search(index='test_index', body = que, request_timeout=timeout)
	return res


def ngrammer(paragraph, n):
    """Extracts all ngrams of length n words from given text"""
    paragraph = paragraph.translate(str.maketrans('', '', string.punctuation))
    ngram = nltk.ngrams(paragraph.split(), n)
    strs = []
    for grams in ngram:
        stri = ' '.join(grams)
        strs.append(stri)
    return list(set(strs))

def check_status(endpoint):
	service = 'es'
	region = 'us-west-2'
	credentials = boto3.Session().get_credentials()
	awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
	es = Elasticsearch( hosts=[endpoint], http_auth=awsauth, use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)
	if(es.ping()):
		return es
	else:
		return False


@app.route('/')
def home():
	return render_template('titlepage.html')

@app.route('/attribution', methods=['POST', 'GET'])
def attribution():
	return render_template('attribution.html')

@app.route('/attributionresult', methods=['POST', 'GET'])
def attributionresult():

	if request.method == 'POST':
		text = request.form['paragraph']


		result = pipeline.predict([text])[0]

		probability = '%.2f'%(max(pipeline.predict_proba([text])[0])*100)
		prob_array = pipeline.predict_proba([text])[0]

		author_list = ['Michael Drayton','Robert Greene','Thomas Kyd', 'Thomas Lodge', 'John Lyly', 'Christopher Marlowe', 'Anthony Munday', 
               'Thomas Nash', 'George Peele', 'Shakespeare', 'Thomas Watson']

		y_pos = np.arange(len(author_list))

		fig = plt.figure(figsize=(20,10))
		ax = fig.add_subplot(1,1,1)
		ax.bar(y_pos, prob_array, align='center', alpha=0.5)
		ax.set_xticks(np.arange(len(author_list)))
		ax.tick_params(labelsize=15)
		ax.set_xticklabels(author_list, rotation=60, fontsize=15)
		ax.set_xlabel('Authors', fontsize=20)
		ax.set_ylabel('Probability', fontsize=20)
		plt.tight_layout()
		plt.savefig('./app/static/attrplot.png')

		return render_template("attributionresult.html",result = result, prob = probability, para=text)

	else:
		return render_template("attribution.html")


@app.route('/ngramsearch', methods=['POST', 'GET'])
def ngramsearch():
	return render_template('ngramsearch.html')

@app.route('/ngramsearchresult', methods=['POST', 'GET'])
def ngramsearchresult():

	if (request.method == 'POST'):
		# get all values from form
		paragraph = request.form['paragraph']
		if (len(paragraph) == 0):
			return render_template('ngramsearch.html')
		exclude_TCP = request.form['tcpid']
		ngram_low = int(request.form['ngram1'])
		ngram_high = int(request.form['ngram2'])
		year_low = int(request.form['year1'])
		year_high = int(request.form['year2'])
		hits_low = int(request.form['hit1'])
		hits_high = int(request.form['hit2'])
		collocation = int(request.form['collocationdist'])
		unknown_year = request.form['yearunknown']
		if (unknown_year == 'yes'):
			unknown_year = True
		else:
			unknown_year = False
		max_results = int(request.form['maxres'])
		author_list = []
		author_flag = True
		for i in range(15):
			auth = 'author' + str(i+1)
			author = request.form[auth]
			if (len(author) > 0):
				author_list.append(author)
		if len(author_list) == 0:
			author_flag = False

		print(exclude_TCP)
		# Create ngrams
		ngram_master_list = []
		for i in range(ngram_low, ngram_high+1):
			ngram_master_list.append(ngrammer(paragraph, i))

		#check if connected to Elasticsearch
		es_inst = check_status(os.environ['ES_ENDPOINT'])

		if (es_inst == False):
			flash('Not connected to elasticsearch!')
			return redirect(request.url)

		result_df = pd.DataFrame(columns = ['ngram', 'total_hits', 'TCP_ID', 'year', 'author', 'title', 'highlight'])
		
		# loop over all ngrams
		for ngram_list in ngram_master_list:
			for ngram in ngram_list:
				if (author_flag):
					init_res = es_query_author(es_inst, year_low, year_high, author_list, ngram, collocation, 0, unknown_year, exclude_TCP)
					if (init_res['hits']['total'] < hits_low or init_res['hits']['total'] > hits_high):
						continue
				else:
					init_res = es_query_no_author(es_inst, year_low, year_high, ngram, collocation, 0, unknown_year, exclude_TCP)
					if (init_res['hits']['total'] < hits_low or init_res['hits']['total'] > hits_high):
						continue

				result = 0
				if (author_flag):
					result = es_query_author(es_inst, year_low, year_high, author_list, ngram, collocation, max_results, unknown_year, exclude_TCP)
				else:
					result = es_query_no_author(es_inst, year_low, year_high, ngram, collocation, max_results, unknown_year, exclude_TCP)

				total_hits = result['hits']['total']

				for hits in result['hits']['hits']:
					TCP_ID = hits['_source']['TCP_ID']
					author = NOS[NOS['TCP_ID'] == TCP_ID].iloc[0]['author']
					title = NOS[NOS['TCP_ID'] == TCP_ID].iloc[0]['title']
					year = NOS[NOS['TCP_ID'] == TCP_ID].iloc[0]['publicationYear']
					
					highlight = ''
					try:
						highlight = highlight.join(hits['highlight']['Text'])
					except:
						pass

					new = pd.DataFrame([[ngram, total_hits, TCP_ID, year, author, title, highlight]], \
						columns = ['ngram', 'total_hits', 'TCP_ID', 'year', 'author', 'title', 'highlight'])
					result_df = result_df.append(new)

		result_df = result_df.drop_duplicates()

		result_df.to_csv('./app/static/NgramResult.csv')



		return render_template('ngramsearchresult.html', ngram = ngram_master_list[0][0])
	else:
		return render_template('ngramsearch.html')


