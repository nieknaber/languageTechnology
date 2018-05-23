import re, operator

def main():

	file = open('Questions language practical', 'r')
	data = file.read().replace('\n', '')
	wordCounts = {'initializeFFF': 0}

	for word in data.split():
		x = re.search('(s\d{7})', word)
		if (x == None):
			wordCounts[word] = (wordCounts.get(word, 0) + 1)

	for w in sorted(wordCounts, key=wordCounts.get, reverse=True):
  		print (w, wordCounts[w])

if __name__ == "__main__":
	main()