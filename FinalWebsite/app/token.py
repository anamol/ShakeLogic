from nltk.stem.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer

def tokenize(text):
		tokenizer = RegexpTokenizer(r'\w+')
		tokens = tokenizer.tokenize(text.lower())
		stems = []
		for item in tokens:
			stems.append(PorterStemmer().stem(item))
		return stems
