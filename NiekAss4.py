import requests, sys, json, re, spacy, fileinput, time
from sys import stdin

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

def search(entity, entOrProp, form = 'normal'): ## make list of entity or property codes
    
    li = searchHelper(entity, entOrProp)
    if(form == 'normal'): li += searchHelper(toSingular(entity), entOrProp)
    return li

def searchAnswer(li, li2): ## search answer, if answer is found, terminate
    check = False ##check if answer has already been given
    sparqlUrl = 'https://query.wikidata.org/sparql'

    q1 = """SELECT ?itemLabel 
    WHERE 
    {"""

    q2 = """
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }"""

    for result in li: ## loop through entities and properties, untill answer is found

        if check: ## if this is true, a proper answer has been given, no need to search further
            return check
        wd = ("{}".format(result['id']))
        
        for result2 in li2:
            if check: ## if this is true, a proper answer has been given, no need to search further
                return check
            wdt = ("{}".format(result2['id']))
            query = q1 + "wd:" + wd + " wdt:" + wdt + " ?item." + q2 ## make query

            answer = requests.get(sparqlUrl,params={'query': query, 'format': 'json'}).json() ## query wikidata
            for item in answer['results']['bindings']:
                    for var in item :
                        ans = ('{}'.format(item[var]['value']))
                        print(ans)
                        check = True ##if there is a proper answer, this is set to true
    return check

def fun(question):

    nlp = spacy.load('en')
    tokenized = nlp(question.strip())
    nouns = list(tokenized.noun_chunks)

    length = len(nouns)
    i = 0
    while i < length: ##delete question words
        if ((nouns[i].text == "what") or (nouns[i].text == "who") or 
        (nouns[i].text == "when") or (nouns[i].text == "where") or 
        (nouns[i].text == "What") or (nouns[i].text == "Who") or 
        (nouns[i].text == "When") or (nouns[i].text == "Where") or
        (nouns[i].text == "an overview") or (nouns[i].text == "overview")):
            del(nouns[i])
            length -= 1
        else:
            i += 1

    if(len(nouns) <= 1):
        print("No answer found. If your question consists of places such as countries, try them with a capital letter")
        return None
    
    x = nouns[0].text
    y = nouns[1].text

    li = search(y, 'entity')
    y = nouns[1].root.lemma_
    li += search(y, 'entity', 'root')

    li2 = search(x, 'property')
    x = nouns[0].root.lemma_
    li2 += search(x, 'property', 'root')

    check = searchAnswer(li, li2)
    if not(check): ## if nothing found try switching property and entity
        check = searchAnswer(li2, li)
        if not(check):
            print("No answer found")
    

def main():
    start = time.time()
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

    print("program took %s seconds" % (time.time() - start))
if __name__ == "__main__":
    main()