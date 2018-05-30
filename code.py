import requests, sys, json, re, spacy, fileinput

#toSingular is a helper function. More helper functions should be specified here
def toSingular(noun):
    if noun.endswith("ies"):
        return noun[:-4] + "y"
    if noun.endswith("ves"):
        return noun[:-4] + "fe"
    if noun.endswith("oes"):
        return noun[:-3]
    elif noun.endswith("es"):
        return noun[:-3]
    elif noun.endswith("s"):
        return noun[:-2]
    elif noun.endswith("i"):
        return noun[:-2] + "us"
    else:
        return noun


def deleteQuestionWords(nouns):
    length = len(nouns)
    i = 0
    while i < length: ##delete question words
        if ((nouns[i].text == "what") or (nouns[i].text == "who") or 
        (nouns[i].text == "when") or (nouns[i].text == "where") or 
        (nouns[i].text == "What") or (nouns[i].text == "Who") or 
        (nouns[i].text == "When") or (nouns[i].text == "Where")):
            del(nouns[i])
            length -= 1
        else:
            i += 1
    return nouns

##here regex specific functions are going to be specified
def whoWhat(question):
    pass

def fun(question):
    
    ## whowhat question Niek
    pattern = '(what |who )(is |are |was |were )(the |a |an |one )?([\w\s\'\-]+? )((of |in |on )(the |a |an |one )?([\w\s\'\-]+)){1,}(\?)?'
    whowhat = re.search(pattern, question, re.IGNORECASE))
	
	
    ##count question Jussi
    pattern = '(how |count )(many )?([\w\s\'\-]+?)(\?)?'
    count = re.search(pattern, question, re.IGNORECASE)
	
	
    ##yesno question Ivo
    pattern = ''
    yesno = re.search(pattern, question, re.IGNORECASE)

    if(whowhat): ##if match with the previous regex...
        pass
    else if(count):
	    #
        pass
    else if(yesno):
        pass


    #try different regex formats of questions. If you get a match, call corresponding function
    #if no regex match is found, try language analysis with spacy


def searchHelper(entity, entOrProp): ## make list of entity or property codes
    url = 'https://www.wikidata.org/w/api.php'
    params = {'action':'wbsearchentities',
        'language':'en',
        'format':'json'}
    params['search'] = entity

    if entOrProp == 'property':
        params['type'] = 'property'

    li = requests.get(url,params).json()['search'] ## search entity
    if(entity.startswith("the ")):
        entity = entity[4:]
        params['search'] = entity
        li += requests.get(url,params).json()['search']
    if(entity.startswith("a ")):
        entity = entity[2:]
        params['search'] = entity
        li += requests.get(url,params).json()['search']
    if(entity.startswith("an ")):
        entity = entity[3:]
        params['search'] = entity
        li += requests.get(url,params).json()['search']
    return li

##searches for the right Q code with a helper function. If mode is raw, which means the raw
## word(s) is given to te funcion, this function also searches for a Q code where it tries to transform 
## the word to singular
def search(entity, entOrProp, form = 'raw'): ## make list of entity or property codes
    
    li = searchHelper(entity, entOrProp)
    if(form == 'raw'): li += searchHelper(toSingular(entity), entOrProp)
    return li

#should be modified, possibly by adding options like form = 'whowhat' or form = 'count'. 
def sparql(li, li2, option = 'normal'): ## search answer, if answer is found, terminate
    
    if(not(option == "normal") and not(option == "count")):
        print("You're using the sparql function wrong: SPECIFIED OPTION NOT AVAILABLE")
    
    check = False ##check if answer has already been given
    sparqlUrl = 'https://query.wikidata.org/sparql'

    cnt = 0

    q1 = """SELECT ?itemLabel 
    WHERE 
    {"""

    q2 = """
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }"""

    for result in li: ## loop through entities and properties, untill answer is found

        if check: ## if this is true, a proper answer has been given, no need to search further
            return check
            print(cnt)
        wd = ("{}".format(result['id']))
        
        for result2 in li2:
            if check: ## if this is true, a proper answer has been given, no need to search further
                print(cnt)
                return check
            wdt = ("{}".format(result2['id']))
            query = q1 + "wd:" + wd + " wdt:" + wdt + " ?item." + q2 ## make query

            answer = requests.get(sparqlUrl,params={'query': query, 'format': 'json'}).json() ## query wikidata
            for item in answer['results']['bindings']:
                    for var in item :
                        if (option == "normal"):
                            ans = ('{}'.format(item[var]['value']))
                            print(ans)
                        else if (option == "count"):
                            cnt +=1

                        check = True ##if there is a proper answer, this is set to true
    return check

def main():

    questions = [
        "The population of Amsterdam is how big?",
        "What nickname has South-Carolina?",
        "What are the timezones of Syria?",
        "Tell the capital of Switzerland?",
        "Who is the king of Norway?",
        "How big is the area covered by the Sahara desert?",
        "In which continent is Gambia located?",
        "What is the highest point in Russia?",
        "Give the width of the Dead Sea",
        "Tell the coordinate location of the St James's Palace?",
        "List the official languages in Belgium?",
        "Give an overview of the official languages in Belgium?"
    ]

    for q in questions:
        print(q)
        fun(q)

    for line in sys.stdin:
        print(line)
        fun(line)


if __name__ == "__main__":
    main()