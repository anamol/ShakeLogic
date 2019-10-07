import numpy as np
import os

def file_compare(root_path):
	xmls = []
	json = []
	for path, subdirs, files in os.walk(root_path):
		for name in files:
			if (name[-3:] == 'xml'):
				filename = os.path.splitext(name)[0]
				xmls.append(filename)
			elif (name[-4:] == 'json'):
				filename = os.path.splitext(name)[0]
				json.append(filename)

	print(len(xmls))
	print(len(json))
	in_xml_not_in_json = np.setdiff1d(xmls, json)
	in_json_not_in_xml = np.setdiff1d(json, xmls)

	print(in_xml_not_in_json)
	print(in_json_not_in_xml)

	with open('in_xml_not_in_json.csv', 'w') as outfile:
		for entries in in_xml_not_in_json:
			outfile.write(entries)
			outfile.write("\n")

	with open('in_json_not_in_xml.csv', 'w') as outfile:
		for entries in in_json_not_in_xml:
			outfile.write(entries)
			outfile.write("\n")


file_compare('.')

