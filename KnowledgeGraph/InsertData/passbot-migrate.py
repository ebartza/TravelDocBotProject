from typedb.client import TypeDB, TransactionType, SessionType
import csv

db = {'db_name':'TravelBotDB','db_server':'localhost:1729'}

def build_passbot_graph(inputs):
    with TypeDB.core_client(db['db_server']) as client:
        with client.session(db['db_name'], SessionType.DATA) as session:
            for input in inputs:
                print("Loading from [" + input["data_path"] + "] into Grakn ...")
                load_data_into_grakn(input, session)

def load_data_into_grakn(input, session):
    items = parse_data_to_dictionaries(input)

    with session.transaction(TransactionType.WRITE) as transaction:
        for item in items:
            graql_insert_query = input["template"](item)
            print("Executing Graql Query: " + graql_insert_query)
            transaction.query().insert(graql_insert_query)
        transaction.commit()

    print("\nInserted " + str(len(items)) + " items from [ " + input["data_path"] + "] into Grakn.\n")


def cost_template(cost):
    # insert cost

    print(cost["identifier"])

    if cost["identifier"] != "":
        graql_insert_query = 'insert $cost isa cost, has identifier "' + cost["identifier"] + '"'
        graql_insert_query += ', has cost_value "' + cost["Value"] + '"'
        graql_insert_query += ', has currency "' + cost["currency"] + '"'
        graql_insert_query += ', has description "' + cost["description"] + '"'
        graql_insert_query += ', has sort_description "' + cost["sort_description"] + '"'
        graql_insert_query += ', has weight ' + str(cost["weight"])  
        graql_insert_query += ";"
        return graql_insert_query

def evidence_template(evidence):
    # insert cost

   if evidence["identifier"] != "":
        graql_insert_query = 'insert $evidence isa evidence, has identifier "' + evidence["identifier"] + '"'
        graql_insert_query += ', has name "' + evidence["name"] + '"'
        graql_insert_query += ', has description "' + evidence["description"] + '"'
        graql_insert_query += ";"
        return graql_insert_query

def output_template(passport):
    # insert cost

    if passport["identifier"] != "":
        graql_insert_query = 'insert $passport isa output, has identifier "' + passport["identifier"] + '"'
        graql_insert_query += ', has name "' + passport["name"] + '"'
        graql_insert_query += ', has description "' + passport["description"] + '"'
        graql_insert_query += ', has description "' + passport["description"] + '"'
        graql_insert_query += ', has weight ' + str(passport["weight"]) 
        graql_insert_query += ";"
        return graql_insert_query

def answers_template(answers):
    # insert answers

    if answers["identifier"] != "":
        graql_insert_query = 'insert $answers isa answers, has identifier "' + answers["identifier"] + '"'
        graql_insert_query += ', has name "' + answers["name"] + '"'
        graql_insert_query += ', has answers_value "' + answers["value"] + '"'
        graql_insert_query += ', has output_identifier "' + answers["output"] + '"'
        graql_insert_query += ', has cost_identifier "' + str(answers["cost"]) + '"'
        graql_insert_query += ";"
        return graql_insert_query

def relations_template(relations):
    # match answer
    graql_insert_query = 'match $user_answer isa answers, has identifier "' + relations["answer_id"] + '";'
    graql_insert_query += '$relative_output isa output, has identifier "' + relations["output_id"] + '";'
    graql_insert_query += 'insert $output_cost_relation (relative-answer-has-output: $user_answer,relative-output-for-answer: $relative_output) isa answer-conserns-output;'
    return graql_insert_query

def answers_evidence_template(relations):
    # match answer
    graql_insert_query = 'match $user_answer isa answers, has identifier "' + relations["answer_id"] + '";'
    graql_insert_query += '$relative_evidence isa evidence, has identifier "' + relations["evidence_id"] + '";'
    graql_insert_query += 'insert $output_cost_relation (relative-answer-excludes-evidence: $user_answer,relative-evidence-excluded-for-answer: $relative_evidence) isa answer-excludes-evidence;'
    return graql_insert_query

def cost_relations_template(relations):
    # match answer
    graql_insert_query = 'match $user_answer isa answers, has identifier "' + relations["answer_id"] + '";'
    graql_insert_query += '$relative_cost isa cost, has identifier "' + relations["cost_id"] + '";'
    graql_insert_query += 'insert $answer_cost_relation (relative-answer-has-cost: $user_answer,relative-cost-for-answer: $relative_cost) isa answer-conserns-cost;'
    return graql_insert_query

def parse_data_to_dictionaries(input):
    items = []
    with open(input["data_path"] + ".csv", encoding='utf-8-sig') as data: # 1
        for row in csv.DictReader(data, skipinitialspace = True):
            item = { key: value for key, value in row.items() }
            items.append(item) # 2
    return items

inputs = [
    {
        "data_path": "data/cost-output-evidence/cost",
        "template": cost_template
    },
    {
        "data_path": "data/cost-output-evidence/evidence",
        "template": evidence_template
    },
    {
        "data_path": "data/cost-output-evidence/output",
        "template": output_template
    },
    {
        "data_path": "data/cost-output-evidence/answers",
        "template": answers_template
    },
    {
        "data_path": "data/cost-output-evidence/relations",
        "template": relations_template
    },
    {
        "data_path": "data/cost-output-evidence/answers-evidence-relation",
        "template": answers_evidence_template
    },
    {
        "data_path": "data/cost-output-evidence/relations",
        "template": cost_relations_template
    }
]

build_passbot_graph(inputs)