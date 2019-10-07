from elasticsearch import Elasticsearch, helpers
import json
import certifi
import os


def check_status(endpoint):
	es = Elasticsearch([endpoint], use_ssl=True, ca_certs=certifi.where())
	print(es.ping())
	return es

def bulk_push_all_json(index, endpoint, path, step=100):

	es = check_status(endpoint)

	if (es.ping() != True):
		print('Not connected to es!')
		return False

	json_files = []
	large_json_files = []
	for path, subdirs, files in os.walk(path):
		for name in files:
			if (name[-4:] == 'json'):
				if (os.stat(os.path.join(path, name)).st_size < 1e7):
					json_files.append(os.path.join(path, name))
				else:
					large_json_files.append(os.path.join(path, name))

	with open('large_json.csv', 'w') as outfile:
		for entries in large_json_files:
			outfile.write(entries)
			outfile.write("\n")

	print('done with looking up json files')

	bulk_json = []
	for jsons in json_files:
		with open(jsons) as json_doc:
			data = json.load(json_doc)

		data.update({"_index": index, "_type": '_doc'})
		bulk_json.append(data)
	print('done with appending to bulk_json')

	try:
		helpers.bulk(es, bulk_json, chunk_size=step)
	except Exception as e:
		print("Err...")
		import pickle
		pickle.dump(e,open("err","wb")) 

def push_all(index, endpoint, path):
	es = check_status(endpoint)

	if (es.ping() != True):
		print('Not connected to es!')
		return False

	json_files = []
	large_json_files = []
	for path, subdirs, files in os.walk(path):
		for name in files:
			if (name[-4:] == 'json'):
				if (os.stat(os.path.join(path, name)).st_size < 1e7):
					json_files.append(os.path.join(path, name))
				else:
					large_json_files.append(os.path.join(path, name))

	with open('large_json.csv', 'w') as outfile:
		for entries in large_json_files:
			outfile.write(entries)
			outfile.write("\n")

	print('done with looking up json files')

	bulk_json = []
	for jsons in json_files:
		with open(jsons) as json_doc:
			data = json.load(json_doc)
		try:
			res = es.index(index = index, body = data)
		except Exception as e:
			print("Err...")
			import pickle
			pickle.dump(e,open("err","wb"))
			with open('errors.csv', 'a+') as outfile:
				outfile.write(jsons)
				outfile.write('\n')
		#data.update({"_index": index, "_type": '_doc'})
		#bulk_json.append(data)
	#print('done with appending to bulk_json')


		
	


index = 'test_index'
endpoint = 'https://search-phase1prod-gyfvdnaek4kwthkpnkfmaclrva.us-west-2.es.amazonaws.com'
path = 'all_json/'
step = 1
#bulk_push_all_json(index, endpoint, path, step)
push_all(index, endpoint, path)


