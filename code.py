import requests, sys, json, re, spacy, fileinput
from optparse import OptionParser
##testtestest
#toSingular is a helper function. More helper functions should be specified here
DEBUG = False

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

    check = False

    li = []
    if(r.status_code == 200):
        # print(r.json())
        answers = r.json()['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['synonyms']
        # print(answers)
        for syn in answers:
            li.append(syn['text'])
        check = True

    if noun == "people":
        li.append("population")
        check = True
    elif noun == "provinces": 
        li.append("contains administrative territorial entity")
        check = True
    elif noun == "citizens":
        li.append("population")
        check = True
    if check:
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
#li = entity, li2 = property
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

    for result in li2: ## loop through entities and properties, untill answer is found
        wdt = ("{}".format(result['id']))
        newLi = []
        if check: ## if this is true, a proper answer has been given, no need to search further
            if(option == "count"):
                    print(cnt)
            elif(option == "silent"):
                return newLi
            return check
        

        for result2 in li:
            if check: ## if this is true, a proper answer has been given, no need to search further
                if(option == "count"):
                    print(cnt)
                elif(option == "silent"):
                    return newLi
                return check
            wd = ("{}".format(result2['id']))
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
                    if DEBUG: print(ans)
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
    prop = prop.strip()
    if prop == 'number' or prop == 'size' or prop == 'amount' :
        print(ans[0])
        return ans
    entQ = search(ans[0], 'entity')
    propQ = search(prop, 'property')
    ans = sparql(entQ, propQ, option)
    return ans

##here regex specific functions are going to be specified
def countQuestion(count):
	
    if(count.group(1) == 'how ' or count.group(1) == 'How '):
        x = count.group(3)
        y = count.group(6)
    else:
        x = count.group(4)
        y = count.group(7)        
	
	#remove 'the'
    x = x.replace("the ", "")
    y = y.replace("the ", "")
    x = x.replace(" run", "")
    y = y.replace(" run", "")

    x = x.strip()
    y = y.strip()
    f = count.group(1).strip().lower()
    
    if (x == 'citizens' or x == 'inhabitants' or x == "people" or x == 'meters' or x == 'kilometers' or y == 'inhabitants' or y == 'meters' or 
    y == 'kilometers' or f == 'return' or f == 'give' or f == 'list' or f == 'name' or f == 'state'): 
        adj = ""
        if not(count.group(2) == None): adj = count.group(2).strip().lower()
        if (adj == "the height" or adj == "the size"):
            return dissolveNP(adj[4:], x + " of " + y)
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
    x = regex.group(4).strip() ## x contains first noun
    y = regex.group(7).strip() ## contains one noun, or a group of multiple nouns seperated by a proposition

    return dissolveNP(x, y)

def whatAre(regex):
    x = regex.group(2).strip()
    y = regex.group(5).strip()

    return dissolveNP(x,y)

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

def flows(regex):
    x = regex.group(2).strip()
    y = regex.group(4).strip()
    
    return dissolveNP(x,y)

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
    length = len(nouns)
    if(length <= 1):
        print("No answer found")
        return None


    # x = nouns[length - 2].text
    # y = nouns[length - 1].text
    i = length - 1
    ans = []
    ans.append(nouns[i])
    prop = nouns[i-1]
    entQ = search(ans[0], 'entity')
    entQ += search(ans[0].root.lemma_, 'entity')
    propQ = search(prop, 'property')
    propQ += search(prop.root.lemma_, 'property', 'root')
    
    while (i>1):
        ans = sparql(entQ, propQ, 'silent')
        if not(ans): sparql(propQ, entQ, 'silent')
        i -= 1
        prop = nouns[i-1]
        entQ = search(ans[0], 'entity')
        propQ = search(prop, 'property')
        propQ += search(prop.root.lemma_, 'property', 'root')
    ans = sparql(entQ, propQ)
    if not(ans): 
        ans2 = sparql(propQ, entQ)
        if not(ans2):
            print("No answer found")
            return False
    else: return ans

def fun(question):
    
    ## whowhat question Niek
    pattern = '^(what |who )(is |are |was |were )(the |a |an |one )?([\w\s\'\-]+? )(of |in |on )(the |a |an |one )?([\w\s\'\-]+?)(\?)?$'
    whowhat = re.search(pattern, question, re.IGNORECASE)
    ## whatare question Niek
    pattern = '^(what |which )([\w\s\'\-]+? )(is |are |was |were )(in |of |part of )([\w\s\'\-]+)(\.|\?)?$'
    whatare = re.search(pattern, question, re.IGNORECASE)
    ## consists question Niek
    pattern = '^([\w\s\'\-]+? )consist(s)? of (which |what )([\w\s\'\-]+)(\?)?$'
    consist = re.search(pattern, question, re.IGNORECASE)
    ## in which question Niek
    pattern = '^in which ([\w\s\'\-]+? )(is |was |are |were )([\w\s\'\-]+?)( located)?(\?)?$'
    inwhich = re.search(pattern, question, re.IGNORECASE)
    ## border question Niek
    pattern = '^which ([\w\s\'\-]+ )(share a )?(border )(with )?([\w\s\'\-]+)(\?)?$'
    border = re.search(pattern, question, re.IGNORECASE)
    ## flow question Niek
    pattern = '^Through (which |what )([\w\s\'\-]+? )(flows |does )([\w\s\'\-]+?)( flow)(\?|\.)?$'
    flow = re.search(pattern, question, re.IGNORECASE)
    ##count questions Jussi
    pattern = '^(how )(many |big )+([\w\s\'\-]+)(is |was |were |are |does |border |has |flow into |are there |are there |live |have )+(in )?([\w\s\'\-]*?)(have| pass through| cross| intersect)?(\?)?$'
    count = re.search(pattern, question, re.IGNORECASE)
    pattern = '^(count |return |give |list |name |state )(the amount |the number |the height |the size |all )?(of |in )?([\w\s\'\-]+? )(that border |that |in |of |belonging to |part of )(flow into )?([\w\s\'\-]+?)?( has| borders| passes through)?(\?)?(\.)?$'
    count2 = re.search(pattern, question, re.IGNORECASE)
	##yesno question Ivo
    pattern = '^(Is |are |were |was )(it )?(true |correct )?(that )?(.*(?= a| part of| has| is| in))?( a | part of | has | is | in )?(.*(?= of | on | the | in ))?( of | on | the | in )?(.*(?=\?))(\?)$'
    yesno = re.search(pattern, question, re.IGNORECASE)


    c = False
    if(whowhat): ##if match with the previous regex...
        if DEBUG: print("whowhat")
        c = whoWhat(whowhat)
    elif(whatare):
        if DEBUG: print("whatare")
        c = whatAre(whatare)
    elif(consist):
        if DEBUG: print("sonsist")
        c = consistOf(consist)
    elif(inwhich):
        if DEBUG: print("inwhich")
        c = inWhich(inwhich)
    elif(border):
        if DEBUG: print("border")
        c = borders(border)
    elif(flow):
        if DEBUG: print("flow")
        c = flows(flow)
    elif(count):
        if DEBUG: print("count")
        c = countQuestion(count)
    elif(count2):
        if DEBUG: print("count2")
        c = countQuestion(count2)
    elif(yesno):
        if DEBUG: print("yesno")
        print(trueFalse(yesno))
        c = True
    if not(c):
        if DEBUG: print("spacy")
        space(question)
    #try different regex formats of questions. If you get a match, call corresponding function
    #if no regex match is found, try language analysis with spacy

def main():

    # parser = OptionParser()
    # parser.add_option("-d", "--debug",
    #                 action="store_false", dest="verbose", default=True,
    #                 help="don't print status messages to stdout")

    # (options, args) = parser.parse_args()
    questions = [
        # "How big is the surface of the sahara desert?",
        # "How many countries border lake Victoria?",
        # "In what country is the Arc de Triomphe located?",
        # "Is Australia a continent?",
        # "List all administrative territorial entities in the Netherlands?",
        # "List the official languages of New Zealand.",
        # "Name the motto of Canada",
        # "On which continent is the Onyx River located?",
        # "State the highest peak in Jamaica",
        # "State the height of the highest peak in Jamaica.", 
        # "Through what countries does the Rhine flow?",
        # "What are the official languages in Belgium?",
        # "What countries are part of the Benelux"
    ]

    for q in questions:
        print(q)
        fun(q)

    for line in sys.stdin:
        print(line)
        fun(line)


if __name__ == "__main__":
    main()