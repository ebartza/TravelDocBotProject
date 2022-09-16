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

    print("\nInserted " + str(len(items)) + " items from [ " + input["data_path"] + "] into TravelBotDB.\n")

def country_template(country):
    if country["identifier"]!="":
    # insert country
        graql_insert_query = 'insert $country isa country, has identifier "' + country["identifier"] + '"'
        graql_insert_query += ', has code "' + country["code"] + '"'
        graql_insert_query += ', has name "' + country["name"] + '"'
        graql_insert_query += ', has capital_name "' + country["capital_name"] + '"'
        graql_insert_query += ', has description "' + country["description"] + '"'
        graql_insert_query += ";"
        return graql_insert_query

def lifeEvent_template(lifeEvent):
    # insert lifeEvent

    if lifeEvent["identifier"] != "":
        graql_insert_query = 'insert $lifeEvent isa lifeEvent, has identifier "' + lifeEvent["identifier"] + '"'
        graql_insert_query += ', has name "' + lifeEvent["name"] + '"'
        graql_insert_query += ', has description "' + lifeEvent["description"] + '"'
        graql_insert_query += ', has lifeEventType "' + lifeEvent["lifeEventType"] + '"'
        graql_insert_query += ";"
        return graql_insert_query

def publicService_template(publicService):
    # insert public service

    if publicService["identifier"] != "":
        graql_insert_query = 'insert $ps isa publicService, has identifier "' + publicService["identifier"] + '"'
        graql_insert_query += ', has name "' + publicService["name"] + '"'
        graql_insert_query += ', has description "' + publicService["description"] + '"'
        graql_insert_query += ";"
        return graql_insert_query

def LE_PSRelation_template(relations):
#     # match lifeEvent and publicService
    graql_insert_query = 'match $le isa lifeEvent, has identifier "' + relations["le_id"] + '";'
    graql_insert_query += '$relative_ps isa publicService, has identifier "' + relations["ps_id"] + '";'
    graql_insert_query += 'insert $relative_ps_relation (relative-LE-Contains-PS: $le,relative-PS-IsGroupedBy-LE: $relative_ps) isa LE-Contains-PS;'
    return graql_insert_query

def publicOrganization_template(publicOrganization):
    # insert publicOrganization
    graql_insert_query = 'insert $ps isa publicOrganization, has identifier "' + publicOrganization["identifier"] + '"'
    graql_insert_query += ', has name "' + publicOrganization["name"] + '"'
    graql_insert_query += ', has preferredLabel "' + publicOrganization["preferredLabel"] + '"'
    graql_insert_query += ";"
    return graql_insert_query

def PO_PSRelation_template(PO_PSRelation):
#     # match lifeEvent and publicService
    graql_insert_query = 'match $po isa publicOrganization, has identifier "' + PO_PSRelation["po_id"] + '";'
    graql_insert_query += '$relative_ps isa publicService, has identifier "' + PO_PSRelation["ps_id"] + '";'
    graql_insert_query += 'insert $relative_ps_relation (relative-PO-issues-PS: $po,relative-PS-issuedBy-PO: $relative_ps) isa PS-hasContentAuthority-PO;'
    return graql_insert_query

def PO_CountyRelation_template(PO_CountryRelation):
        # match publicOrganization with Country
        graql_insert_query = 'match $po isa publicOrganization, has identifier "' + PO_CountryRelation["po_id"] + '";'
        graql_insert_query += '$relative_country isa country, has identifier "' + PO_CountryRelation["country_id"] + '";'
        graql_insert_query += 'insert $relative_po_relation (relative-PO-isLocatedAt-Country: $po,relative-Country-Locates-PO: $relative_country) isa PO-IsLocatedAt-Country;'
        return graql_insert_query


def PS_RulesRelation_template(PS_RulesRelation):
        # match publicService with Rules
        graql_insert_query = 'match $ps isa publicService, has identifier like "(' + PS_RulesRelation["PS_id"] + ')";'
        graql_insert_query += '$relative_rules isa rules, has identifier "' + PS_RulesRelation["Ru_id"] + '";'
        graql_insert_query += 'insert $relative_ps_relation (relative-PS-follows-rules: $ps,relative-rules-isFollowedFor-PS: $relative_rules) isa PS-follows-rules;'
        return graql_insert_query

def PS_ChannelsRelation_template(PS_ChannelRelation):
        # match publicService with Channels
        graql_insert_query = 'match $ps isa publicService, has identifier "' + PS_ChannelRelation["PS_id"] + '";'
        graql_insert_query += '$relative_Channels isa channel, has identifier "' + PS_ChannelRelation["Ch_id"] + '";'
        graql_insert_query += 'insert $relative_channel_relation (relative-PS-has-channels: $ps,relative-channels-toAccess-PS: $relative_Channels) isa PS-has-channels;'
        return graql_insert_query

def PS_EvidenceRelation_template(PS_EvidenceRelation):
        # match publicService with Channels
        graql_insert_query = 'match $ps isa publicService, has identifier "' + PS_EvidenceRelation["PS_id"] + '";'
        graql_insert_query += '$relative_Evidence isa evidence, has identifier like "(' + PS_EvidenceRelation["Ev_id"] + ')";'
        graql_insert_query += 'insert $relative_evidence_relation (relative-PS-Has-Evidence: $ps,relative-Evidence-InputFor-PS: $relative_Evidence) isa PS-HasInput-Evidence;'
        return graql_insert_query

def PS_OutputRelation_template(PS_OutputRelation):
        # match publicService with Output
        graql_insert_query = 'match $ps isa publicService, has identifier like "' + PS_OutputRelation["PS_id"] + '";'
        graql_insert_query += '$relative_Output isa output, has identifier "' + PS_OutputRelation["Ou_id"] + '";'
        graql_insert_query += 'insert $relative_output_relation (relative-PS-Produces-Output: $ps,relative-Output-ProducedFor-PS: $relative_Output) isa PS-Produces-Output;'
        return graql_insert_query

def Output_CountryRelation_template(Output_CountryRelation):
        # match publicService with Output
        graql_insert_query = 'match $ou isa output, has identifier "' + Output_CountryRelation["Ou_id"] + '";'
        graql_insert_query += '$relative_Country isa country, has identifier like "(' + Output_CountryRelation["Country_id"] + ')";'
        graql_insert_query += 'insert $relative_Country_relation (relative-Output-isValidFor-Country: $ou,relative-Country-HasValid-Output: $relative_Country) isa Output-IsValidFor-Country;'
        return graql_insert_query
def Rules_ChannelRelation_template(Rules_ChannelRelation):
        # match publicService with Output
        graql_insert_query = 'match $ru isa rules, has identifier "' + Rules_ChannelRelation["Ru_id"] + '";'
        graql_insert_query += '$relative_Channel isa channel, has identifier like "' + Rules_ChannelRelation["Ch_id"] + '";'
        graql_insert_query += 'insert $relative_Channel_relation (relative-rules-ifaccessedThrough-channel: $ru,relative-channel-accessedThrough-rules: $relative_Channel) isa Rules-ifAccessedThrough-channel;'
        return graql_insert_query

def Evidence_ChannelRelation_template(Evidence_ChannelRelation):
        # match evidence with channel
        graql_insert_query = 'match $ev isa evidence, has identifier "' + Evidence_ChannelRelation["Ev_id"] + '";'
        graql_insert_query += '$relative_Channel isa channel, has identifier like "' + Evidence_ChannelRelation["Ch_id"] + '";'
        graql_insert_query += 'insert $relative_Channel_relation (relative-evidence-for-channel: $ev,relative-Channel-has-Evidence: $relative_Channel) isa Channel-has-Evidence;'
        return graql_insert_query

def Cost_PSRelation_template(Cost_PSRelation):
        # match publicService with cost
        graql_insert_query = 'match $co isa cost, has identifier "' + Cost_PSRelation["co_id"] + '";'
        graql_insert_query += '$relative_PS isa publicService, has identifier "' + Cost_PSRelation["ps_id"] + '";'
        graql_insert_query += 'insert $relative_PS_relation (relative-Cost-For-PS: $co,relative-PS-Has-Cost: $relative_PS) isa PS-Has-Cost;'
        return graql_insert_query

def Cost_ChannelRelation_template(Cost_ChannelRelation):
        # match cost with channel
        graql_insert_query = 'match $co isa cost, has identifier  "' + Cost_ChannelRelation["co_id"] + '";'
        graql_insert_query += '$relative_Channel isa channel, has identifier "' + Cost_ChannelRelation["ch_id"] + '";'
        graql_insert_query += 'insert $relative_Channel_relation (relative-cost-ifAccessedThrough-channel: $co,relative-channel-accessedThrough-cost: $relative_Channel) isa Cost-ifAccessedThrough-channels;'
        return graql_insert_query

def Cost_AnswersRelation_template(Cost_AnswersRelation):
        # match cost with asnwers
        graql_insert_query = 'match $user_answer isa answers, has identifier like "' + Cost_AnswersRelation["an_id"] + '";'
        graql_insert_query += '$relative_cost isa cost, has identifier "' + Cost_AnswersRelation["co_id"] + '";'
        graql_insert_query += 'insert $answer_cost_relation (relative-answer-has-cost: $user_answer,relative-cost-for-answer: $relative_cost) isa answer-conserns-cost;'
        return graql_insert_query

def PS_QuestionsRelation_template(PS_QuestionsRelation):
        # match publicSevice with Questions
        graql_insert_query = 'match $qu isa questions, has identifier like "' + PS_QuestionsRelation["Q_id"] + '";'
        graql_insert_query += '$relative_PS isa publicService, has identifier "' + PS_QuestionsRelation["ps_id"] + '";'
        graql_insert_query += 'insert $relative_PS_relation (relative-Questions-Fulfilled-PS: $qu,relative-PS-Fulfills-Questions: $relative_PS) isa PS-Fulfills-Questions;'
        return graql_insert_query

def Output_AnswersRelation_template(Output_AnswersRelation):
        # match output with asnwers
        graql_insert_query = 'match $user_answer isa answers, has identifier like "(' + Output_AnswersRelation["an_id"] + ')";'
        graql_insert_query += '$relative_output isa output, has identifier "' + Output_AnswersRelation["ou_id"] + '";'
        graql_insert_query += 'insert $output_cost_relation (relative-answer-has-output: $user_answer,relative-output-for-answer: $relative_output) isa answer-conserns-output;'
        return graql_insert_query 


def Questions_AnswersRelation_template(Questions_AnswersRelation_template):
        # match questions with asnwers
        graql_insert_query = 'match $user_answer isa answers, has identifier like "(' + Questions_AnswersRelation_template["A_id"] + ')";'
        graql_insert_query += '$relative_Questions isa questions, has identifier "' + Questions_AnswersRelation_template["Q_id"] + '";'
        graql_insert_query += 'insert $Answers_Questions_relation (realtive-answer-answers-question: $user_answer,relative-question-has-answers: $relative_Questions) isa questions-have-answers;'
        return graql_insert_query 

def Channel_AnswersRelation_template(Channel_AnswersRelation_template):
        # match channel with asnwers
        graql_insert_query = 'match $user_answer isa answers, has identifier like "(' + Channel_AnswersRelation_template["A_id"] + ')";'
        graql_insert_query += '$relative_Channel isa channel, has identifier "' + Channel_AnswersRelation_template["Ch_id"] + '";'
        graql_insert_query += 'insert $Answers_Channel_relation (relative-answer-concerns-channel: $user_answer,relative-channel-for-answer: $relative_Channel) isa Answer-concerns-channel;'
        return graql_insert_query 

def answers_evidence_template(relations):
    # match answer
    graql_insert_query = 'match $user_answer isa answers, has identifier like "(' + relations["A_id"] + ')";'
    graql_insert_query += '$relative_evidence isa evidence, has identifier "' + relations["Ev_id"] + '";'
    graql_insert_query += 'insert $answers_evidence_relation (relative-answer-excludes-evidence: $user_answer,relative-evidence-excluded-for-answer: $relative_evidence) isa answer-excludes-evidence;'
    return graql_insert_query

def CostTravel_template(Cost):
        # insert Cost 
      graql_insert_query = 'insert $co isa cost, has identifier "' + Cost["identifier"] + '"'
      graql_insert_query += ', has description "' + Cost["description"] + '"'
      graql_insert_query += ', has cost_value "' + Cost["cost_value"] + '"'
      graql_insert_query += ', has currency "' + Cost["currency"] + '"'
      graql_insert_query += ', has comment "' + Cost["comment"] + '"'
      graql_insert_query += ', has weight ' + str(Cost["weight"])  
      graql_insert_query += ', has processingTime "' + Cost["processingTime"] + '"'
      graql_insert_query += ";"
      return graql_insert_query

def OutputTravel_template(Output):
        # insert Output 
      graql_insert_query = 'insert $ou isa output, has identifier "' + Output["identifier"] + '"'
      graql_insert_query += ', has description "' + Output["description"] + '"'
      graql_insert_query += ', has name "' + Output["name"] + '"'
      graql_insert_query += ', has categoryDuration "' + Output["categoryDuration"] + '"'
      graql_insert_query += ', has category "' + Output["category"] + '"'
      graql_insert_query += ', has weight ' + str(Output["weight"])  
      graql_insert_query += ";"
      return graql_insert_query

def Channel_template(Channel):
        # insert Channel 
      graql_insert_query = 'insert $ch isa channel, has identifier "' + Channel["identifier"] + '"'
      graql_insert_query += ', has channelType "' + Channel["channelType"] + '"'
      graql_insert_query += ', has name "' + Channel["name"] + '"'
      graql_insert_query += ', has phone "' + Channel["phone"] + '"'
      graql_insert_query += ', has serviceURL "' + Channel["serviceURL"] + '"'
      graql_insert_query += ', has address "' + Channel["address"] + '"'    
      graql_insert_query += ', has email "' + Channel["email"] + '"'
      graql_insert_query += ', has hoursAvailable "' + Channel["hoursAvailable"] + '"'
      graql_insert_query += ', has processingTime "' + Channel["processingTime"] + '"'
      graql_insert_query += ";"
      return graql_insert_query

def Rules_template(Rules):
        # insert Rules 
      graql_insert_query = 'insert $ru isa rules, has identifier "' + Rules["identifier"] + '"'
      graql_insert_query += ', has name "' + Rules["name"] + '"'
      graql_insert_query += ', has description "' + Rules["description"] + '"'
      graql_insert_query += ', has sort_description "' + Rules["sort_description"] + '"'
      graql_insert_query += ";"
      return graql_insert_query

def Evidence_template(Evidence):
        # insert Evidence 
      graql_insert_query = 'insert $ev isa evidence, has identifier "' + Evidence["identifier"] + '"'
      graql_insert_query += ', has name "' + Evidence["name"] + '"'
      graql_insert_query += ', has description "' + Evidence["description"] + '"'
      graql_insert_query += ";"
      return graql_insert_query

def Questions_template(Questions):
        # insert Questions 
      graql_insert_query = 'insert $ev isa questions, has identifier "' + Questions["identifier"] + '"'
      graql_insert_query += ', has description "' + Questions["description"] + '"'
      graql_insert_query += ', has aa "' + Questions["aa"] + '"'
      graql_insert_query += ";"
      return graql_insert_query

def Answers_template(Answers):
        # insert Questions 
      graql_insert_query = 'insert $ev isa answers, has identifier "' + Answers["identifier"] + '"'
      graql_insert_query += ', has name "' + Answers["name"] + '"'
      graql_insert_query += ";"
      return graql_insert_query     


def parse_data_to_dictionaries(input):
    items = []
    with open(input["data_path"] + ".csv", encoding='utf-8-sig') as data: # 1
        for row in csv.DictReader(data, skipinitialspace = True):
            item = { key: value for key, value in row.items() }
            items.append(item) # 2
    return items

inputs = [
    # Entities
    {
        "data_path": "data/csv/lifeEvent",
        "template": lifeEvent_template
    },
    {
        "data_path": "data/csv/Country",
        "template": country_template
    },
    {
        "data_path": "data/csv/publicService",
       "template":publicService_template
    },
 
    {
        "data_path": "data/csv/Cost",
       "template":CostTravel_template
    } ,
     {
        "data_path": "data/csv/Output",
       "template":OutputTravel_template
    } ,
{
        "data_path": "data/csv/Channel",
       "template":Channel_template
    } ,
{
       "data_path": "data/csv/Rules",
       "template":Rules_template
    } ,
{
       "data_path": "data/csv/Evidence",
       "template":Evidence_template
    } ,
   {
        "data_path": "data/csv/Answers",
       "template":Answers_template
    } ,
  {
        "data_path": "data/csv/Questions",
       "template":Questions_template
    } ,

    {
        "data_path": "data/csv/Relations/LE_PSRelations",
       "template":LE_PSRelation_template
    },
{
        "data_path": "data/csv/publicOrganization",
       "template":publicOrganization_template
    },
#   # Relations
    {
        "data_path": "data/csv/Relations/publicOrganizationToPublicService",
       "template":PO_PSRelation_template
    },
  {
        "data_path": "data/csv/Relations/publicOrganizationToCountry",
       "template":PO_CountyRelation_template
    },
  
    {
        "data_path": "data/csv/Relations/RulestoPS",
       "template": PS_RulesRelation_template
    },
      {
        "data_path": "data/csv/Relations/PSToChannel",
       "template": PS_ChannelsRelation_template
    } ,
     {
        "data_path": "data/csv/Relations/EvidencetoPS",
       "template": PS_EvidenceRelation_template
    } 
,
  {
        "data_path": "data/csv/Relations/EvidenceToChannel",
       "template": Evidence_ChannelRelation_template
    } 
,
       {
        "data_path": "data/csv/Relations/outputToPS",
       "template": PS_OutputRelation_template
    } ,

       {
        "data_path": "data/csv/Relations/OutputoCountry",
       "template": Output_CountryRelation_template
    } 
    ,
      {
        "data_path": "data/csv/Relations/RulesToChannel",
       "template": Rules_ChannelRelation_template
    } ,
    {
        "data_path": "data/csv/Relations/CostToPublicService",
       "template": Cost_PSRelation_template
    } ,

     {
        "data_path": "data/csv/Relations/CostToChannel",
       "template": Cost_ChannelRelation_template
    } , 
    {
        "data_path": "data/csv/Relations/CostToAnswers",
       "template": Cost_AnswersRelation_template
    } ,
     {
        "data_path": "data/csv/Relations/PSToQuestions",
       "template": PS_QuestionsRelation_template
    } ,
 {
        "data_path": "data/csv/Relations/QuestionsToAnswers",
       "template": Questions_AnswersRelation_template
    } ,
     {
        "data_path": "data/csv/Relations/ChannelToAnswer",
       "template": Channel_AnswersRelation_template
    } ,
     {
        "data_path": "data/csv/Relations/EvidenceToAnswers",
       "template": answers_evidence_template
    } 

    ]
build_passbot_graph(inputs)