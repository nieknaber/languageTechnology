import requests, sys, json, re, spacy, fileinput
##testtestest
#toSingular is a helper function. More helper functions should be specified here
def toSingular(noun):
    noun = noun.strip()
    if noun.endswith("ies"):
        return [noun[:-3] + "y"]
    elif noun.endswith("ves"):
        return [noun[:-3] + "fe"]
    elif noun.endswith("oes"):
        return [noun[:-2]]
    elif noun.endswith("es"):
        return [noun[:-2], noun[:-1]]
    elif noun.endswith("s"):
        return [noun[:-1]]
    elif noun.endswith("i"):
        return [noun[:-1] + "us"]
    return []


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

## get synonyms of the word using the oxford dictionary
def getSynonym(noun):
    noun = noun.strip() 
    app_id = ' 08ce8597'
    app_key = 'a2a7e6f4e846dc42b4571bb8f57ca15d'

    language = 'en'
    word_id = noun

    url = 'https://od-api.oxforddictionaries.com:443/api/v1/entries/' + language + '/' + word_id.lower() + '/synonyms'

    r = requests.get(url, headers = {'app_id': app_id, 'app_key': app_key})

    li = []
    if(r.status_code == 200):
        # print(r.json())
        answers = r.json()['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['synonyms']
        # print(answers)
        for syn in answers:
            li.append(syn['text'])
        return li
    return False

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
def search(noun, entOrProp, form = 'raw'): ## make list of entity or property codes
    
    li = searchHelper(noun, entOrProp)
    if(form == 'raw' and (entOrProp == "property")): 
        single = toSingular(noun)
        for entry in single:
            li += searchHelper(entry, entOrProp)
    if(entOrProp == 'property' and form == 'raw'): 
        synonym = getSynonym(noun)
        if (not synonym == False):
            for entry in synonym:
                li += searchHelper(entry, entOrProp)
    return li

#should be modified, possibly by adding options like form = 'whowhat' or form = 'count'. 
def sparql(li, li2, option = 'normal'): ## search answer, if answer is found, terminate
    
    if(not(option == "normal") and not(option == "count") and not(option == "silent")):
        print("You're using the sparql function wrong: SPECIFIED OPTION NOT AVAILABLE")
        return False
    
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
        wd = ("{}".format(result['id']))
        newLi = []
        if check: ## if this is true, a proper answer has been given, no need to search further
            if(option == "count"):
                    print(cnt)
            elif(option == "silent"):
                return newLi
            return check
        

        for result2 in li2:
            if check: ## if this is true, a proper answer has been given, no need to search further
                if(option == "count"):
                    print(cnt)
                elif(option == "silent"):
                    return newLi
                return check
            wdt = ("{}".format(result2['id']))
            query = q1 + "wd:" + wd + " wdt:" + wdt + " ?item." + q2 ## make query

            answer = requests.get(sparqlUrl,params={'query': query, 'format': 'json'}).json() ## query wikidata
            for item in answer['results']['bindings']:
                    for var in item :
                        if (option == "normal"):
                            ans = ('{}'.format(item[var]['value']))
                            print(ans)
                        elif(option == "silent"):
                            ans = ('{}'.format(item[var]['value']))
                            newLi.append(ans)
                        elif (option == "count"):
                            cnt +=1

                        check = True ##if there is a proper answer, this is set to true
    if(option == "count"):
        print(cnt)
    elif(option == "silent"):
        return newLi
    return check 

def sparqlTF(list_subj1, subj2, list_prop, mode = 'normal'):
    #Figure out the question formats and the type of answer they require
    #Do sparql lookup, loop through answer list for match
    #Return true/false

    if(not(mode == "normal")):
        print("You're using the sparql function wrong: SPECIFIED OPTION NOT AVAILABLE")
        return False

    sparqlUrl = 'https://query.wikidata.org/sparql'
    q1 = """SELECT ?itemLabel 
    WHERE 
    {"""
    q2 = """
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }"""

    for q_code in list_subj1:
         wd = ("{}".format(q_code['id']))
         for p_code in list_prop:
            wdt = ("{}".format(p_code['id']))
            query = q1 + "wd:" + wd + " wdt:" + wdt + " ?item." + q2
            answer = requests.get(sparqlUrl,params={'query': query, 'format': 'json'}).json()
            for item in answer['results']['bindings']:
                 for var in item :
                    ans = ('{}'.format(item[var]['value']))
                    print(ans)
                    if (ans.lower() == subj2.lower()):
                        return True

    return False

##x = entity, y = property
def dissolveNP(x, y, option = 'normal'):
    li = []
    li.append(x)

    pattern = '(the |a |an |one )?([\w\s\'\-]+? )(of |in |on )(the |a |an |one )?([\w\s\'\-]+?)(\?)?$'
    se = re.search(pattern, y, re.IGNORECASE)
    
    while(se):
        x = se.group(2)
        y = se.group(5)
        li.append(x)
        se = re.search(pattern, y, re.IGNORECASE)
    li.append(y)
    ########################################### list of properties/nouns has been made

    i = len(li) - 1

    ans = []
    ans.append(li[i])

    while (i>1):
        prop = li[i-1]
        entQ = search(ans[0], 'entity')
        propQ = search(prop, 'property')
        ans = sparql(entQ, propQ, 'silent')
        i -= 1
    prop = li[i-1]
    entQ = search(ans[0], 'entity')
    propQ = search(prop, 'property')
    ans = sparql(entQ, propQ, option)
    return ans

##here regex specific functions are going to be specified
def countQuestion(count):
	#assign the entity and relation to x and y
    #x = count.group(3)
    #y = count.group(6)
	
    if(count.group(1) == 'how ' or count.group(1) == 'How '):
        x = count.group(3)
        y = count.group(6)
    else:
        x = count.group(4)
        y = count.group(7)        


 #   if(count.group(1) == 'how ' or count.group(1) == 'How '):
  #      if count.group(4).strip() == 'border':
  #          x = 'shares border with'
  #      else:
  #          x = count.group(3)
  #      y = count.group(6)
  #  else:
  #      if count.group(5).strip() == 'that border' or count.group(8).strip() == 'borders':
  #          x = 'shares border with'
  #      else:
  #          x = count.group(4)
  #      y = count.group(7)        	
    #print('x', x, 'y', y)
	
	#remove 'the' and replace some relations with synonyms as they are noted in wikidata
    x = x.replace("the ", "")
    y = y.replace("the ", "")
    x = x.replace(" run", "")
    y = y.replace(" run", "")
    x = x.replace("provinces ", "contains administrative territorial entity")
    y = y.replace("provinces ", "contains administrative territorial entity")
    x = x.replace("citizens ", "inhabitants")
    y = y.replace("citizens ", "inhabitants")	
    #print('x', x, 'y', y)

    if (x == 'inhabitants' or x == 'meters' or x == 'kilometers' or y == 'inhabitants' or y == 'meters' or y == 'kilometers'): 
	    return dissolveNP(x, y)
    else:
	    return dissolveNP(x, y, 'count')

def trueFalse(regex):
    subj1 = regex.group(5) 
    subj2 = regex.group(9)
    conjunction = regex.group(6).strip() #use this to filter question types
    prop = regex.group(7)

    list_subj1 = search(subj1, "entity")
    list_subj2 = search(subj2, "entity")

    if (prop != None):
        list_prop = search(prop, "property")
        return sparqlTF(list_subj1, subj2, list_prop)

    if (conjunction == "a" or conjunction == "an"): # Is X a Y --> prop is instance of
        list_prop = search("instance of", "property")
        return sparqlTF(list_subj1, subj2, list_prop)

    if (conjunction == "part of"):
        list_prop = search("part of", "property")
        return sparqlTF(list_subj1, subj2, list_prop)

    return "reached end of function without result"

    #1 Make lists of properties and q/r codes
    #2 determine question type, and so search format (mode in sparqlTF)
    #3 Additional Regex/SpaCy filter for divergent question formats

def whoWhat(regex): 
    x = regex.group(4) ## x contains first noun
    y = regex.group(7) ## contains one noun, or a group of multiple nouns seperated by a proposition

    return dissolveNP(x, y)

def consistOf(regex):
    x = regex.group(4).strip()
    y = regex.group(1).strip()

    return dissolveNP(x,y)
    
def inWhich(regex):
    x = regex.group(1).strip()
    y = regex.group(3).strip()
    
    return dissolveNP(x,y)

def borders(regex):
    x = regex.group(1).strip()
    y = regex.group(5).strip()
    
    check = dissolveNP(x,y)
    if not(check):
        x = 'shares border with'
        return dissolveNP(x,y)
    else:
        return True

def space(question):

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
        print("No answer found")
        return None
    
    x = nouns[0].text
    y = nouns[1].text

    li = search(y, 'entity')
    y = nouns[1].root.lemma_
    li += search(y, 'entity', 'root')

    li2 = search(x, 'property')
    x = nouns[0].root.lemma_
    li2 += search(x, 'property', 'root')

    check = sparql(li, li2)
    if not(check): ## if nothing found try switching property and entity
        check = sparql(li2, li)
        if not(check):
            print("No answer found")



def fun(question):
    
    ## whowhat question Niek
    pattern = '(what |who )(is |are |was |were )(the |a |an |one )?([\w\s\'\-]+? )(of |in |on )(the |a |an |one )?([\w\s\'\-]+?)(\?)?$'
    whowhat = re.search(pattern, question, re.IGNORECASE)
    ## consists question Niek
    pattern = '([\w\s\'\-]+? )consist(s)? of (which |what )([\w\s\'\-]+)(\?)?$'
    consist = re.search(pattern, question, re.IGNORECASE)
    ## in which question Niek
    pattern = 'in which ([\w\s\'\-]+? )(is |was |are |were )([\w\s\'\-]+?)( located)?(\?)?$'
    inwhich = re.search(pattern, question, re.IGNORECASE)
    ## border question Niek
    pattern = 'which ([\w\s\'\-]+ )(share a )?(border )(with )?([\w\s\'\-]+)(\?)?$'
    border = re.search(pattern, question, re.IGNORECASE)
    ##count questions Jussi
    pattern = '(how )(many )+([\w\s\'\-]+)(does |border |has |flow into |are there |are there)+(in )?([\w\s\'\-]*?)(have| pass through| cross| intersect)?(\?)?$'
    count = re.search(pattern, question, re.IGNORECASE)
    pattern = '(count |return |give |list )(the amount |the number )(of )?([\w\s\'\-]*?)(that border |that |in |belonging to |part of )(flow into )?([\w\s\'\-]+?)?( has| borders| passes through)?(\?)?(\.)?$'
    count2 = re.search(pattern, question, re.IGNORECASE)
	##yesno question Ivo
    pattern = '(Is |are |were |was )(it )?(true |correct )?(that )?(.*(?= a| part of| has| is| in))?( a | part of | has | is | in )?(.*(?= of | on | the ))?( of | on | the )?(.*(?=\?))(\?)$'
    yesno = re.search(pattern, question, re.IGNORECASE)


    c = False
    if(whowhat): ##if match with the previous regex...
        c = whoWhat(whowhat)
    elif(consist):
        c = consistOf(consist)
    elif(inwhich):
        c = inWhich(inwhich)
    elif(border):
        c = borders(border)
    elif(count):
	    c = countQuestion(count)
    elif(count2):
	    c = countQuestion(count2)
    elif(yesno):
        print(trueFalse(yesno))
        c = True
    if not(c):
        space(question)
    #try different regex formats of questions. If you get a match, call corresponding function
    #if no regex match is found, try language analysis with spacy

def main():

    questions = [
        "list the amount of rivers that flow into Lake Superior?",
        "Which countries border Switzerland?",
        "Scandinavia consists of which countries?",
        "In which country is Amsterdam located?",
        "What is the population of the capital of the Netherlands?",
        "What are the timezones of Syria?",
        "What is the highest point in Russia?"
    ]

    for q in questions:
        print(q)
        fun(q)

    for line in sys.stdin:
        print(line)
        fun(line)


if __name__ == "__main__":
    main()