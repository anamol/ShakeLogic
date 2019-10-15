import os
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import concurrent.futures
import json
import nltk
import string
from tei_reader import TeiReader

def download_from_bitbucket():
	""" Downloads all files from Bitbucket phase1texts 

	Input: None

	Output: None  """

	for i in range(96):
		if (i < 10):
			cmd = 'git clone ssh://anamolpundle@bitbucket.org/shcdemo/a0' + str(i) + '.git'
		else:
			cmd = 'git clone ssh://anamolpundle@bitbucket.org/shcdemo/a' + str(i) + '.git'

		os.system(cmd)

	cmd = 'git clone ssh://anamolpundle@bitbucket.org/shcdemo/a97.git'
	os.system(cmd)
	cmd = 'git clone ssh://anamolpundle@bitbucket.org/shcdemo/a99.git'


	for i in range(10):
		
		cmd = 'git clone ssh://anamolpundle@bitbucket.org/shcdemo/b0' + str(i) + '.git'

		os.system(cmd)

	b = [11,13,15,21,22]

	for ctr in b:
		cmd = 'git clone ssh://anamolpundle@bitbucket.org/shcdemo/b' + str(ctr) + '.git'
		os.system(cmd)

def get_text_tei(input_xml):
	""" Returns text in string form using TEI reader given an input XML document in TEI format

	Input: Path to XML document in TEI format

	Output: Text in string format """

	reader = TeiReader()
	corpora = reader.read_file(input_xml)
	teststr = corpora.text
	return teststr


def get_text(input_xml):
	""" Returns text in string form using BeautifulSoup, given an input XML document in TEI format. Replaces with 
	regularized form if present in XML tag

	Input: Path to XML document in TEI format

	Output: Text in string format """

    infile = open(input_xml)
    contents = infile.read()
    soup = BeautifulSoup(contents,'lxml')
    
    text = ""
    my_dict = {}
    lines = soup.find_all('text')
    for line in lines:
        new_line = ""
        words = line.find_all(['w', 'pc'])
        for word in words:
            if word.has_attr('reg'):
                new_line = new_line + word['reg'] + " "

                if (word.get_text() not in my_dict):
                	my_dict[word.get_text()] = word['reg']

            else:
                new_line = new_line + word.get_text() + " "
        text = text + new_line
    return [text, my_dict]

def build_JSON(title, author, year, TCP_ID, text):
	""" Returns JSON (python dictionary) object given data from XML documents 

	Input: Doc Title, Doc Author, Publication year, TCP_ID, and Doc text

	Output: JSON object  """

	JSON = { 'Title': title,
	'Author' : author,
	'Year' : year,
	'TCP_ID': TCP_ID,
	'Text': text
	}

	return JSON

def multithread(root_path, df, workers=8):
	""" Multithreaded code that takes all XML documents in root path (including subfolders), converts to and saves as JSON. 
	Creates  dictionary of words that have regularized spelling in XML tags and saves as dictionary.json. 

	Input: root path, NOS dataframe, number of workers for multithreading 

	Output: None  """

	# find all XMLS in root_path
	xmls = []
	all_dicts = []
	for path, subdirs, files in os.walk(root_path):
		for name in files:
			if (name[-3:] == 'xml'):
				xmls.append(os.path.join(path, name))
	print(xmls)

	with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
	# Start the load operations and mark each future with its URL

		future_to_url = {executor.submit(get_text, xml): xml for xml in xmls}
		for future in concurrent.futures.as_completed(future_to_url):
			xml_file = future_to_url[future]
			try:
				data = future.result()[0]	          
			except Exception as exc:
				print('%r generated an exception: %s' % (xml_file, exc))
			else:
				all_dicts.append(future.result()[1])
				filename = os.path.basename(xml_file)
				filename_noext = os.path.splitext(filename)[0]
				df2 = df[df['path_to_file'].str.contains(filename)]
				title = df2['title'].iloc[0]
				author = df2['author'].iloc[0]
				year = df2['publicationYear'].iloc[0]
				TCP_ID = df2['TCP_ID'].iloc[0]
				text = data
				JSON = build_JSON(title, author, year, TCP_ID, text)

				# Save as json in json/ folder in root_path
				with open('json/' + filename_noext + '.json', 'w') as outfile:
					json.dump(JSON, outfile)
				print('done!')
    
	final_dict = {}

	for ctr, diction in enumerate(all_dicts):
		final_dict.update(diction)

	# save dictionary as json
	with open('dictionary.json', 'w') as output:
		json.dump(final_dict, output)

def ngrammer(paragraph, n):
    """Extracts all ngrams of length n words from given text. Returns list of ngrams. """
    paragraph = paragraph.translate(str.maketrans('', '', string.punctuation))
    ngram = nltk.ngrams(paragraph.split(), n)
    strs = []
    for grams in ngram:
        stri = ' '.join(grams)
        strs.append(stri)
    return strs
	            

df = pd.read_excel('NOS_database_table_of_contents.xls', sheet_name='phase1_table_of_contents')
print('done')
multithread('XMLs/', df)








