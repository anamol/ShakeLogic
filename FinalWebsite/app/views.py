# views.py

from flask import  Flask, render_template, Response
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
import random
from matplotlib import pyplot as plt
import numpy as np


from app import app

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
pipeline = joblib.load('pipeline.joblib')


def es_ngram_query(es, ngram, collocation):
	que = { 
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

	res = es.search(index='test_index', body = que)
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
    #es = Elasticsearch([endpoint])
	if(es.ping()):
		return es
	else:
		return False


@app.route('/attribution', methods=['POST', 'GET'])
def attribution():
	return render_template('attribution.html')

@app.route('/attributionresult', methods=['POST', 'GET'])
def attributionresult():

	if request.method == 'POST':
		text = request.form['paragraph']

		#if (len(text) < 1000):
		#	return render_template("notenoughwords.html")

		result = pipeline.predict([text])[0]

		probability = '%.2f'%(max(pipeline.predict_proba([text])[0])*100)
		prob_array = pipeline.predict_proba([text])[0]

		author_list = ['Drayton','Robert Greene','Lodge', 'Lyly', 'Christopher Marlowe', 'Anthony Munday', \
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
		#plt.savefig('/Users/anamolpundle/Documents/Insight/FinalWebsite/app/static/attrplot.png')

		return render_template("attributionresult.html",result = result, prob = probability, para=text)

	else:
		return render_template("attribution.html")


@app.route('/ngramsearch', methods=['POST', 'GET'])
@app.route('/', methods=['POST', 'GET'])
def ngramsearch():
	return render_template('ngramsearch.html')

@app.route('/ngramsearchresult', methods=['POST', 'GET'])
def ngramsearchresult():
	if (request.method == 'POST'):
		paragraph = request.form['paragraph']
		if (len(paragraph) == 0):
			flash('Entr\'th m\'re words than none!')
			return render_template('ngramsearch.html')
		excude_TCP = request.form['tcpid']
		ngram_low = int(request.form['ngram1'])
		ngram_high = int(request.form['ngram2'])
		year_low = int(request.form['year1'])
		year_high = int(request.form['year2'])
		hits_low = int(request.form['hit1'])
		hits_high = int(request.form['hit2'])
		collocation = int(request.form['collocationdist'])
		"""author1 = request.form['author1']
		author2 = request.form['author2']
		author3 = request.form['author3']
		author4 = request.form['author4']
		author5 = request.form['author5']"""
		unknown_year = request.form['yearunknown']
		author_list = []
		for i in range(15):
			auth = 'author' + str(i+1)
			author = request.form[auth]
			if (len(author) > 0):
				author_list.append(author)

		ngram_master_list = []
		for i in range(ngram_low, ngram_high+1):
			ngram_master_list.append(ngrammer(paragraph, i))

		es_inst = check_status('https://search-phase1prod-gyfvdnaek4kwthkpnkfmaclrva.us-west-2.es.amazonaws.com')

		if (es_inst == False):
			flash('Not connected to elasticsearch!')
			return redirect(request.url)

		result_df = pd.DataFrame(columns = ['ngram', 'hits', 'TCP_ID', 'year', 'author', 'title', 'highlight'])

		for ngram_list in ngram_master_list:
			for ngram in ngram_list:
				result = es_ngram_query(es_inst, ngram, collocation)
				if (result['hits']['total'] >= hits_low and result['hits']['total'] <= hits_high):
					for hits in result['hits']['hits']:
						author = hits['_source']['Author']
						title = hits['_source']['Title']
						year = hits['_source']['Year']
						total_hits = result['hits']['total']
						TCP_ID = hits['_source']['TCP_ID']
						highlight = ''
						try:
							highlight = highlight.join(hits['highlight']['Text'])
						except:
							pass
						if (isinstance(year, numbers.Number)):
							if (year >= year_low and year <= year_high):
								new = pd.DataFrame([[ngram, total_hits, TCP_ID, year, author, title, highlight]], \
									columns = ['ngram', 'hits', 'TCP_ID', 'year', 'author', 'title', 'highlight'])
								result_df = result_df.append(new)
						elif (unknown_year == 'yes' and not isinstance(year, numbers.Number)):
							new = pd.DataFrame([[ngram, total_hits, TCP_ID, year, author, title, highlight]], \
									columns = ['ngram', 'hits', 'TCP_ID', 'year', 'author', 'title', 'highlight'])
							result_df = result_df.append(new)


		result_df = result_df.drop_duplicates()
		result_df = result_df[result_df['TCP_ID'] != excude_TCP]
		final_df = pd.DataFrame(columns = ['ngram', 'hits', 'TCP_ID', 'year', 'author', 'title', 'highlight'])
		if (len(author_list) > 0):
			for author in author_list:
				new = result_df[result_df['author'].str.contains(author)]
				final_df = final_df.append(new)
		else:
			final_df = result_df
		

		final_df.to_csv('./app/static/NgramResult.csv')



		return render_template('ngramsearchresult.html', ngram = ngram_master_list[0][0])
	else:
		return render_template('ngramsearch.html')


