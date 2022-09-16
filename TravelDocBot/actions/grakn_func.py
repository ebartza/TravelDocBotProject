from typedb.client import *
from inspect import *

def get_query_for_travelbot(query,param):
   if query == 'about_visa':
        aboutVisa_query = f"""
            match 
            $y isa rules,has name "VISA ABOUT",has description $d; 
            get $y,$d;offset 0; limit 1;
            """
        return aboutVisa_query       

   if query == 'about_ekaa':
        aboutEkaa_query = f"""
            match 
            $y isa rules,has name "EKAA ABOUT",has description $d; 
            get $y,$d;sort $d desc;
            """ 
        return aboutEkaa_query

   if query == 'Procedure_ekaa':
        ProcedureEkaa_query = f"""
            match 
            $rules isa rules, has name "EKA ISSUE PROCEDURE", has identifier like  "({param})"; 
            $rules has description $d, has identifier $i;
            get $rules,$d; sort $d asc;
    
            """ 
        return ProcedureEkaa_query
        
   if query == 'Procedure_ekaa_University':
        ProcedureEkaaUni_query = f"""
           match
		   $channel isa channel, has name contains "{param}";
            $ru isa rules, has name "EKKA UNIVERSITY ISSUE PROC", has description $d, has identifier $i;
            $relative_Channel_relation (relative-rules-ifaccessedThrough-channel: $ru,relative-channel-accessedThrough-rules: $channel) isa Rules-ifAccessedThrough-channel;
            get $d,$i;

            """ 
        return ProcedureEkaaUni_query

   if query == 'Countries_ekaa':
        CountriesEkaa_query = f"""
     match 
        $output isa output, has identifier "Ou0007";
        $country isa country, has name $n;
        $rel (relative-Country-HasValid-Output:$country, relative-Output-isValidFor-Country:$output) isa Output-IsValidFor-Country;
	    get $country,$n;
            """ 
        return CountriesEkaa_query

   if query == 'Country_ekaa':
        CountryEkaa_query = f"""
       match
        $output isa output, has identifier "Ou0007";
        $country isa country, has name $n;
        $country has capital_name like "{param}";
        $rel (relative-Country-HasValid-Output:$country, relative-Output-isValidFor-Country:$output) isa Output-IsValidFor-Country;
	    get $country,$n;
            """ 
        return CountryEkaa_query

   if query == 'WhoCanHave_ekaa':
        WhoCanHaveEkaa_query = f"""
            match 
            $y isa rules,has name "WHO CAN HAVE EKAA",has description $d, has identifier $i; 
            get $y,$i,$d; sort $i asc;
            """ 
        return WhoCanHaveEkaa_query

   if query == 'Duration_ekaa':
        Duration_ekaa_query = f"""
            match 
            $ou isa output, has identifier "Ou0007", has category $c;
            get $ou,$c;
            """ 
        return Duration_ekaa_query
        
   if query == "procedure_of_visa":
        procedure_of_visa_query = f"""
            match $ru isa rules, has name "VISA ISSUE PROCEDURE", has description $descr,has identifier $i;
            $country isa country, has name $name;
            $country has capital_name contains "{param}";
            $rel (relative-Rule-IsDefined-Country: $ru, relative-Country-Defines-Rule: $country) isa Rule-IsDefinedBy-Country;
            get $ru,$descr,$i; sort $i asc;
            """  
        return procedure_of_visa_query

   if query == "Find_Embassy":
        Embassy_query = f"""
            match 
            $ch isa channel, has name $n, has address $a, has email $em, has phone $ph, has hoursAvailable $ha;
            $country isa country, has capital_name contains "{param}";
            $answers isa answers, has identifier "A0091";
            $answerForCh (relative-channel-for-answer:$ch,relative-answer-concerns-channel:$answers) isa Answer-concerns-channel;
            $chForCountry (relative-Channel-empoweredBy-Country: $ch, relative-Country-empoweres-Channel: $country) isa Channel-isPoweredBy-Country;
            get $n,$a,$em,$ph,$ha;
        """
        return Embassy_query

   if query == "Find_Embassy_Rest":
        Embassy_query_Rest = f"""
            match 
            $ch isa channel, has name $n, has address $a, has email $em, has phone $ph, has hoursAvailable $ha, has identifier $id ;
            $country isa country, has capital_name contains "{param}";
            $chForCountry (relative-Channel-empoweredBy-Country: $ch, relative-Country-empoweres-Channel: $country) isa Channel-isPoweredBy-Country;
            get $n,$a,$em,$ph,$ha,$id;sort $id desc;
        """
        return Embassy_query_Rest

   if query == "Find_evisa":
        evisa_query = f"""
            match 
            $ch isa channel, has name $n, has serviceURL $s;
            $country isa country, has capital_name contains "{param}";
            $answers isa answers, has identifier "A0090";
            $answerForCh (relative-channel-for-answer:$ch,relative-answer-concerns-channel:$answers) isa Answer-concerns-channel;
            $chForCountry (relative-Channel-empoweredBy-Country: $ch, relative-Country-empoweres-Channel: $country) isa Channel-isPoweredBy-Country;
            get $n,$s;
        """
        return evisa_query

   if query == "Find_onArrival":
        onArrival_query = f"""
            match 
            $ch isa channel, has name $n, has address $a;
            $country isa country, has capital_name contains "{param}";
            $answers isa answers, has identifier "A0092";
            $answerForCh (relative-channel-for-answer:$ch,relative-answer-concerns-channel:$answers) isa Answer-concerns-channel;
            $chForCountry (relative-Channel-empoweredBy-Country: $ch, relative-Country-empoweres-Channel: $country) isa Channel-isPoweredBy-Country;
            get $n,$a;
        """
        return onArrival_query
   
   if query == 'all_evidence_channel':
        all_evidence_channel = f"""
        match
        $ch isa channel, has name contains "{param}";
        $ev isa evidence, has name $name, has description $descr, has identifier $id;
        $relEv (relative-Channel-has-Evidence:$ch, relative-evidence-for-channel:$ev)isa Channel-has-Evidence;
        get $ev,$name,$descr,$id;sort $id asc;
        """
        return all_evidence_channel

   if query == "visa_duration_Tourist":
        visa_duration_Tourist_query = f"""
            match 
            $ou isa output, has name $n, has categoryDuration $cd, has category $c;
            $n contains "Τουριστική";
            $country isa country, has capital_name contains "{param}";
            $rel (relative-Output-isValidFor-Country: $ou, relative-Country-HasValid-Output: $country) isa Output-IsValidFor-Country;
            get $ou,$n,$cd,$c;
        """
        return visa_duration_Tourist_query

   if query == "visa_duration_Transit":
        visa_duration_Transit_query = f"""
            match 
            $ou isa output, has name $n, has categoryDuration $cd, has category $c;
            $n contains "Transit";
            $country isa country, has capital_name contains "{param}";
            $rel (relative-Output-isValidFor-Country: $ou, relative-Country-HasValid-Output: $country) isa Output-IsValidFor-Country;
            get $ou,$n,$cd,$c;
        """
        return visa_duration_Transit_query

   if query == "Find_Country_Channels":
        Channels_query = f"""
            match 
            $ch isa channel, has identifier $i;
            $country isa country, has capital_name contains "{param}";
            $rel (relative-Channel-empoweredBy-Country: $ch, relative-Country-empoweres-Channel: $country) isa Channel-isPoweredBy-Country;
            get $ch,$i;
        """
        return Channels_query

   if query == "ChannelsTypeForCountry":
        ChannelsForCountry_query = f"""
            match 
            $country isa country, has capital_name contains "{param}";
            $answers isa answers, has identifier $i;
            $rel (relative-Answers-ForChannel-Country: $answers, relative-Country-Answers-Channel: $country) isa Country-HasAnswersFor-Channel;
            get $answers,$i;
        """
        return ChannelsForCountry_query

   if query == "evidence_answerForCountry":
        evidence_answer_query = f"""
        match 
        $country isa country, has capital_name contains "{param[0]}";
        $answers isa answers, has identifier like "({param[1]})";
        $an isa answers, has identifier $id; 
        $all (relative-Answers-ForEvidenceOf-Channel:$an, relative-Channel-ForEvidenceOf-Answers:$ch) isa Channel-HasAnswersFor-Evidence;         
        $answerForCh (relative-channel-for-answer:$ch,relative-answer-concerns-channel:$answers) isa Answer-concerns-channel;
        $chForCountry (relative-Channel-empoweredBy-Country: $ch, relative-Country-empoweres-Channel: $country) isa Channel-isPoweredBy-Country;
        get $id;
        """
        return evidence_answer_query

   if query =="Exclude_evidenceForCountryAndChannel":
        channel_answer_query = f"""
         match
        $country isa country, has capital_name contains "{param[0]}";
        $answers isa answers, has identifier like "({param[1]})";
        $an isa answers, has identifier like "({param[2]})"; 
        $ev isa evidence, has name $name, has description $descr;
        $rel (relative-answer-excludes-evidence:$an,relative-evidence-excluded-for-answer:$ev) isa answer-excludes-evidence;
        $chtoEv (relative-Channel-has-Evidence:$ch, relative-evidence-for-channel:$ev) isa Channel-has-Evidence;
        $answerForCh (relative-channel-for-answer:$ch,relative-answer-concerns-channel:$answers) isa Answer-concerns-channel;
        $chForCountry (relative-Channel-empoweredBy-Country: $ch, relative-Country-empoweres-Channel: $country) isa Channel-isPoweredBy-Country;
        get $name,$descr;
        """
        return channel_answer_query
       
   if query =="all_evidenceForCountryAndChannel":
        channel_answer_query = f"""
            match
            $country isa country, has capital_name contains "{param[0]}";
            $answers isa answers, has identifier like "({param[1]})";
            $ev isa evidence, has name $name, has description $descr;
            $rel (relative-Channel-empoweredBy-Country: $ch, relative-Country-empoweres-Channel: $country) isa Channel-isPoweredBy-Country;
            $relAns (relative-channel-for-answer:$ch, relative-answer-concerns-channel:$answers) isa Answer-concerns-channel;
            $relEv (relative-Channel-has-Evidence:$ch, relative-evidence-for-channel:$ev)isa Channel-has-Evidence;
            get $name,$descr;
            """
        return channel_answer_query
       
   if query =="AnswersOfCostForCountry":
        country_cost_answer_query = f"""
        match 
     	$country isa country,has capital_name contains "{param}";
        $cost isa cost;
        $answer isa answers, has identifier $i;
        $CostCountry(relative-Cost-PSPoweredBy-Country: $cost, relative-Country-PSPowers-Cost: $country) isa Cost-PSPoweredBy-Country;
        $rel (relative-cost-for-answer:$cost,relative-answer-has-cost:$answer) isa answer-conserns-cost;
 		get $i;
        """
        return country_cost_answer_query

   if query =="CostForCountry":
        country_cost_query = f"""
            match 
     	    $country isa country, has capital_name contains "{param[0]}";
            $cost isa cost, has cost_value $n, has currency $c, has description $d;
            $answer isa answers, has identifier like "({param[1]})";
            $answer has identifier $i;
            $CostCountry(relative-Cost-PSPoweredBy-Country: $cost, relative-Country-PSPowers-Cost: $country) isa Cost-PSPoweredBy-Country;
            $rel (relative-cost-for-answer:$cost,relative-answer-has-cost:$answer) isa answer-conserns-cost;
 		    get $n,$c,$d,$i;
            """
        return country_cost_query;  

   if query =="CostForCountryID":
        country_cost_query = f"""
            match 
     	    $country isa country, has capital_name contains "{param[0]}";
            $cost isa cost, has identifier $i;
            $answer isa answers, has identifier like "({param[1]})";
            $CostCountry(relative-Cost-PSPoweredBy-Country: $cost, relative-Country-PSPowers-Cost: $country) isa Cost-PSPoweredBy-Country;
            $rel (relative-cost-for-answer:$cost,relative-answer-has-cost:$answer) isa answer-conserns-cost;
 		    get $i;
            """
        return country_cost_query;      
   if query =="CostForID":
        country_costID_query = f"""
        match
        $cost isa cost, has cost_value $n, has currency $c, has description $d;
        $cost has identifier like "{param}" ;
        get $n,$c,$d;
        """
        return country_costID_query

   if query == 'countries_need_visa':
        countries_need_visa = f"""
            match $ps isa publicService, has name $n ;
            $n contains "Έκδοση visa";
            $country isa country, has name $name;
            $rel (relative-PS-IsLocatedAt-Country: $ps,relative-Country-LocatesFor-PS: $country) isa PS-IsLocatedAt-Country;
            get $country,$name; 
        """
        return countries_need_visa

   if query == 'country_need_visa':
        country_need_visa = f"""
            match $ps isa publicService, has name contains "Έκδοση visa";
            $country isa country, has capital_name contains "{param}", has identifier $id;
            $rel (relative-PS-IsLocatedAt-Country: $ps,relative-Country-LocatesFor-PS: $country) isa PS-IsLocatedAt-Country;
            get $country,$id; 
        """
        return country_need_visa

def get_query_string(query,string_answers):
    if query == 'cost_query':
        cost_query = f"""
            match 
            $y isa cost, has weight $w, has cost_value $n, has currency $c,has sort_description $sd;
            $x isa answers, has identifier like "{string_answers}"; 
            $rel (relative-answer-has-cost:$x,relative-cost-for-answer:$y) isa answer-conserns-cost;
            get $y,$w,$n,$c,$sd; sort $w asc;offset 0; limit 1;
        """
        return cost_query




    if query == 'output_query':
        output_query = f"""
            match 
            $y isa output, has weight $w, has name $n;
            $x isa answers, has identifier like "{string_answers}"; 
            $rel (relative-answer-has-output:$x,relative-output-for-answer:$y) isa answer-conserns-output;
            get $y,$w,$n; sort $w asc;offset 0; limit 1;
        """
        return output_query

    if query == 'excluded_evidence':
        excluded_evidence = f"""
            match
            $ev isa evidence, has name $n, has description $d, has identifier $i;
            $an isa answers, has identifier like "{string_answers}"; 
            $ps isa publicService, has identifier "ps0001";
            $rel (relative-answer-excludes-evidence:$an,relative-evidence-excluded-for-answer:$ev) isa answer-excludes-evidence;
            $relPS (relative-PS-Has-Evidence:$ps,relative-Evidence-InputFor-PS:$ev) isa PS-HasInput-Evidence;
            get $i,$n;
        """
        return excluded_evidence

    if query == 'all_evidence':
        all_evidence = f"""
            match 
            $ev isa evidence, has name $n, has description $d,has identifier $i;
            $ps isa publicService, has identifier "ps0001";
            $rel (relative-PS-Has-Evidence:$ps,relative-Evidence-InputFor-PS:$ev) isa PS-HasInput-Evidence;
            get $ev,$n;

        """
        return all_evidence


    return ''
             
def query_grakn(rasa_query):

    db_name = 'TravelBotDB' # set db name
    db_server = 'localhost:1729' #set db password

    with TypeDB.core_client(db_server) as client:
        with client.session(db_name, SessionType.DATA) as session:
            print('connected to :' + db_name)
            options = TypeDBOptions.core()
            options.infer = True # enable reasoning
            with session.transaction(TransactionType.READ,options) as transaction:
                answers = [ans.map() for ans in transaction.query().match(rasa_query)]
                values = []
                for thing in answers:
                    values.append({ 
                        str(attribute.get_type().get_label()):attribute.get_value() 
                        for attribute in thing.values() 
                        if not attribute.is_entity()
                    })

                return values

def find_list_diff(list1,list2):
    return [ item for item in list1 if item not in list2]

def find_list_common(list1, list2):
    return [item for item in list1 if item in list2]
