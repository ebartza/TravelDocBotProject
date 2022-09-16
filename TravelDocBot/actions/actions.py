from msilib.schema import Class
from select import select
from typing import Any, Text, Dict, List, Union, Optional
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk import ValidationAction

from rasa_sdk.types import DomainDict, TypedDict
from rasa_sdk.events import (
    SlotSet,
    AllSlotsReset,
    UserUtteranceReverted,
    ConversationPaused,
    EventType,
    ActionExecuted,
    UserUttered,
)
import mysql.connector
import unicodedata as ud
import csv
import json
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_validator import validate_email, EmailNotValidError
from sklearn.decomposition import TruncatedSVD
from sqlalchemy import false, null, true

# relative path imports
from . import const
from . import grakn_func as gf


config = const.config

INTENT_DESCRIPTION_MAPPING_PATH = "intent_description_mapping.csv"
GOOGLE_MAP_ADDRESS = "https://www.google.com/maps/place/"
 
LOGIN_EMAIL = const.LOGIN_EMAIL
PASSWORD = const.PASSWORD
SENDER_EMAIL = const.SENDER_EMAIL

BUTTON_YES = "Ναι ✔" 
BUTTON_NO = "Όχι, δεν χρειάζεται ✖"
IDENTIFIER_PS_PASSPORT = "Ps0001"

class ResetAllSlots(Action):

    def name(self) -> Text:
        return "action_reset_all_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:       
        return[AllSlotsReset(), SlotSet("selected_category", "Initial")]

class ActionResetAllButFewSlots(Action):

	def name(self):
		return "action_reset_all_but_few_slots"

	def run(self, dispatcher, tracker, domain):
		country = tracker.get_slot('country')        
		return [AllSlotsReset(), SlotSet("country", country)]

class ActionResetAllButMainSlots(Action):

	def name(self):
		return "action_reset_all_slots_ButMain"

	def run(self, dispatcher, tracker, domain):
		selected_category = tracker.get_slot('selected_category')
		return [AllSlotsReset(), SlotSet("selected_category", selected_category)]


class ActionCategoryPassportSlots(Action):

	def name(self):
		return "action_set_Passport_Category"

	def run(self, dispatcher, tracker, domain):
		return [SlotSet("selected_category", "passport")]

class ActionCategoryVisaSlots(Action):

	def name(self):
		return "action_set_Visa_Category"

	def run(self, dispatcher, tracker, domain):
		return [SlotSet("selected_category", "visa")]

class ActionEkaaVisaSlots(Action):

	def name(self):
		return "action_set_Ekaa_Category"

	def run(self, dispatcher, tracker, domain):
		return [SlotSet("selected_category", "ekaa")]


class ActionDbAboutEkaa(Action):
    # Τι είναι ΕΚΑΑ
    def name(self):
        return "action_db_about_Ekaa"
        
    def run(self, dispatcher, tracker, domain):
        my_ekaaAbout_query = gf.get_query_for_travelbot('about_ekaa','')
        str_data = ""
        about = gf.query_grakn(my_ekaaAbout_query)
        for line in about:
            str_data += line.get('description') + "\n"
        dispatcher.utter_message(str_data)
        return [] 

class ActionDbCountriesEkaa(Action):
    # Για ποιες χώρες ισχύει η ΕΚΑΑ
    def name(self):
        return "action_db_Countries_Ekaa"
        
    def run(self, dispatcher, tracker, domain):
        my_ekaaProcedure_query = gf.get_query_for_travelbot('Countries_ekaa','')
        countries = gf.query_grakn(my_ekaaProcedure_query)
        str_data = "Η Ε.Κ.Α.Α ισχύει στις εξής χώρες: \n"
        for row in countries:
                country = row['name']
                str_data = str_data + country + ","
        str_data = str_data[:-1]
        dispatcher.utter_message(str_data)
        return [] 


class ActionDbDetailsForVisa(Action):
    # Για ποιες χώρες υπάρχουν λεπτομέρειες
    def name(self):
        return "action_db_Countries_Details"
        
    def run(self, dispatcher, tracker, domain):

        SelectedCountry = tracker.get_slot("country")
        d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
        SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
        if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
            SelectedCountry = SelectedCountry[:-1]
        my_visaForCountry_query = gf.get_query_for_travelbot('procedure_of_visa',SelectedCountry)
        grakn_values = gf.query_grakn(my_visaForCountry_query)

        if (len(grakn_values)>0):
            return [SlotSet("DetailsVisa",  "True")]     
        else:
            return [SlotSet("DetailsVisa", "False")]  

class ActionDbWhoCanHaveEkaa(Action): 
# Ποιος μπορεί να εκδόσει ΕΚΑΑ
    def name(self):
        return "action_db_WhoCanHave_Ekaa"
        
    def run(self, dispatcher, tracker, domain):
        my_ekaaProcedure_query = gf.get_query_for_travelbot('WhoCanHave_ekaa','')
        descriptions = gf.query_grakn(my_ekaaProcedure_query)
        str_data = ""
        for descr in descriptions:
            str_data += descr.get('description')
    
        dispatcher.utter_message(str_data)
        return [] 

class ActionDbProcedureEkaa(Action):
# Διαδικασίες εκδοσης ΕΚΑΑ για ανασφάλιστους φοιτητές
    def name(self):
        return "action_db_Procedure_Ekaa"
        
    def run(self, dispatcher, tracker, domain):
        SelectedUniversity = tracker.get_slot('Student_University')
        RuleFilter =""
        str_data = "🗨 "
        Unidescriptions =[]
        UniEvidence = []
        descriptions = []
        if (SelectedUniversity == None):
            RuleFilter = "Ru0115|Ru0116"
        else:
                RuleFilter = "Ru0117"
                d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
                SelectedUniversity = ud.normalize('NFD',SelectedUniversity).upper().translate(d)                
                UnivercityProcedure_query = gf.get_query_for_travelbot('Procedure_ekaa_University',SelectedUniversity)
                Unidescriptions = gf.query_grakn(UnivercityProcedure_query)

                UnivercityEvidence_query = gf.get_query_for_travelbot('all_evidence_channel',SelectedUniversity)
                UniEvidence= gf.query_grakn(UnivercityEvidence_query)
          
        if ((SelectedUniversity == None) or  ((SelectedUniversity != None) and len(Unidescriptions)==0)):
            my_ekaaProcedure_query = gf.get_query_for_travelbot('Procedure_ekaa',RuleFilter)
            descriptions = gf.query_grakn(my_ekaaProcedure_query)
            if (len(descriptions)> 0):
                str_data +=  descriptions[0].get('description') + "\n"
        if (len(Unidescriptions)> 0):
            str_data += Unidescriptions[0].get('description') + "\n"                
        
        if len(UniEvidence)> 0:
            str_data += "Τα δικαιολογητικά 📄 που απαιτούνται είναι τα εξής: \n"
            for evidence in UniEvidence:
                str_data += f"- {evidence.get('name')}\n"
                str_data += evidence.get('description') + "\n"
        else:
            str_data += "Δεν απαιτούνται δικαιολογητικά.\n"      
        dispatcher.utter_message(str_data)
        return [] 

class ActionDbCountriesNeedVisa(Action):
# Ποιες χώρες απαιτούν visa
    def name(self):
        return "action_db_countries_need_visa"
        
    def run(self, dispatcher, tracker, domain):
        my_visaAbout_query = gf.get_query_for_travelbot('countries_need_visa','')
        grakn_values = gf.query_grakn(my_visaAbout_query)
        str_data = ""
        for row in grakn_values:
            country = row['name']
            str_data = str_data + country + ","
        str_data = str_data[:-1]
        dispatcher.utter_message('Οι χώρες που απαιτούν έκδοση βίζα είναι οι ακόλουθες: ' + str_data)
        return [SlotSet("needVisa", None),SlotSet("country", None)] 

class ActionDbCountryNeedVisa(Action):
    # Χρειάζεται η χώρα βίζα;
    def name(self):
        return "action_db_this_country_need_visa"
        
    def run(self, dispatcher, tracker, domain):
        SelectedCountry = tracker.get_slot("country")

        d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
        SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
        if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
            SelectedCountry = SelectedCountry[:-1]
        my_visaForCountry_query = gf.get_query_for_travelbot('country_need_visa',SelectedCountry)
        grakn_values = gf.query_grakn(my_visaForCountry_query)
        if (len(grakn_values)>0):
            return [SlotSet("needVisa",  "True")]     
        else:
            return [SlotSet("needVisa", "False")]  
            
class ActionDbAboutVisa(Action):
# Τι είναι βίζα
    def name(self):
        return "action_db_about_visa"
        
    def run(self, dispatcher, tracker, domain):
        my_visaAbout_query = gf.get_query_for_travelbot('about_visa','')
        grakn_values = gf.query_grakn(my_visaAbout_query)
        description = grakn_values[0]
        str_data = description.get('description')
        dispatcher.utter_message(str_data)
        return [] 

class ActionDbCountryIssueVisa(Action):
# Διαδικασία έκδοσης βίζα
    def name(self):
        return "action_db_visa_issue_procedure"
        
    def run(self, dispatcher, tracker, domain):
        SelectedCountry = tracker.get_slot("country")
        d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
        SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
        if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
            SelectedCountry = SelectedCountry[:-1]
        my_visaForCountry_query = gf.get_query_for_travelbot('procedure_of_visa',SelectedCountry)
        grakn_values = gf.query_grakn(my_visaForCountry_query)
        if (len(grakn_values)>0):
            descr =""
            for row in grakn_values:
                descr = descr + row.get('description') + "\n"
            dispatcher.utter_message(descr)
        else:
            my_EmbassyForCountry_query = gf.get_query_for_travelbot('Find_Embassy',SelectedCountry)
            visa_values = gf.query_grakn(my_EmbassyForCountry_query)
            if (len(visa_values)==0):
                EmbassyForCountry_query = gf.get_query_for_travelbot('Find_Embassy_Rest',SelectedCountry)
                visa_values = gf.query_grakn(EmbassyForCountry_query)
            if (len(visa_values)>0):
                name = visa_values[0].get('name')
                address = visa_values[0].get('address')
                email =  visa_values[0].get('email')
                phone =  visa_values[0].get('phone')
                hoursAvailable = visa_values[0].get('hoursAvailable')
                str =  "Επικοινώνησε με την {0}, \nΔιεύθυνση: {1}".format(name,address)
                if (phone != ''):
                    str = str + "\nΤηλ.:"+ phone               
                if (email != ''):
                    str = str + "\nEmail:"+ email
                if (hoursAvailable !=''):
                    str = str + "\nΏρες κοινού:"+hoursAvailable
                dispatcher.utter_message(str)
            else:
                dispatcher.utter_message("Για στοιχεία επικοινωνίας πρεσβείας/προξενείου και περισσότερες πληροφορίες απευθυνθείτε στο Υπουργείο Εξωτερικών.")
        return []

class ActionDbCountryDurationVisa(Action):
# Διάρκεια visa
    def name(self):
        return "action_db_visa_duration"
        
    def run(self, dispatcher, tracker, domain):
        SelectedCountry = tracker.get_slot("country")
        d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
        SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
        if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
            SelectedCountry = SelectedCountry[:-1]
        my_visaduration_query = gf.get_query_for_travelbot('visa_duration_Tourist',SelectedCountry)
        grakn_values = gf.query_grakn(my_visaduration_query)
        str_data = ""
        found = false
        if (len(grakn_values)>0):
            found = true
            str_data = "\n "
            for row in grakn_values:
                category = row['category']
                if (category!=''):
                     str_data = str_data +  " Τουριστική βίζα με διάρκεια " + category 
                categoryDuration = row['categoryDuration']
                if (categoryDuration!=''):
                     str_data = str_data +  " " + categoryDuration   
                str_data = str_data + "."

        my_visaduration_query = gf.get_query_for_travelbot('visa_duration_Transit',SelectedCountry)
        grakn_values = gf.query_grakn(my_visaduration_query)
        if (len(grakn_values)>0):
            found=true
            str_data = str_data+ "\n Βίζα διέλευσης "
            for row in grakn_values:
                category = row['category']
                if (category!=''):
                    str_data = str_data +  "με διάρκεια ως εξής : " + category 
                else:
                    str_data = str_data +  "με περιορισμένη διάρκεια"
               
                str_data = str_data + "."
            str_data = str_data[:-1]
        if (found == false):
            dispatcher.utter_message('Δεν γνωρίζω λεπτομέρειες για την επιλεγμένη χώρα.')
        else:
            dispatcher.utter_message('Για την επιλεγμένη χώρα μπορείς να εκδόσεις : ' + str_data)
        return [] 

class ActionDbCountryEmbassy(Action):
    def name(self):
        return "action_db_Place_Of_Submission_Visa_Embassy"
        
    def run(self, dispatcher, tracker, domain):

        SelectedCountry = tracker.get_slot("country")
        d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
        SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
        if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
            SelectedCountry = SelectedCountry[:-1]
        my_EmbassyForCountry_query = gf.get_query_for_travelbot('Find_Embassy',SelectedCountry)
        visa_values = gf.query_grakn(my_EmbassyForCountry_query)
        if (len(visa_values)<=0):
            my_EmbassyForCountry_query = gf.get_query_for_travelbot('Find_Embassy_Rest',SelectedCountry)
            visa_values = gf.query_grakn(my_EmbassyForCountry_query)        
        if (len(visa_values)>0):
            name = visa_values[0].get('name')
            address = visa_values[0].get('address')
            email =  visa_values[0].get('email')
            
            phone =  visa_values[0].get('phone')
            hoursAvailable = visa_values[0].get('hoursAvailable')
            str =  "Για έκδοση βίζα επικοινώνησε με την {0}, \nΔιεύθυνση: {1}".format(name,address)
            if (phone != ''):
                str = str + "\nΤηλ.:"+ phone               
            if (email != ''):
                str = str + "\nEmail:"+ email
            if (hoursAvailable !=''):
                str = str + "\nΏρες κοινού:"+hoursAvailable
            dispatcher.utter_message(str)
        else:
            dispatcher.utter_message("Για ενημέρωση σχετικά με την πρεσβεία/προξενείο επικοινώνησε με το Υπουργείο Εξωτερικών για περισσότερες λεπτομέρειες.")
        return [] 

class ActionDbCountryeVisa(Action):
    def name(self):
        return "action_db_Place_Of_Submission_eVisa"

    def run(self, dispatcher, tracker, domain):
       
        SelectedCountry = tracker.get_slot("country")
        d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
        SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
        if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
            SelectedCountry = SelectedCountry[:-1]
        evisaForCountry_query = gf.get_query_for_travelbot('Find_evisa',SelectedCountry)
        visa_values = gf.query_grakn(evisaForCountry_query)
        if (len(visa_values)>0):
            name = visa_values[0].get('name')
            address = visa_values[0].get('serviceURL')
            str =  "Μπορείς να εκδόσεις την βίζα ηλεκτρονικά στην τοποθεσία: \n{0}".format(address)
            dispatcher.utter_message(str)
        return [] 

class ActionDbCountryVisaonArrival(Action):
    def name(self):
        return "action_db_Place_Of_Submission_Visa_OnArrival"
        
    def run(self, dispatcher, tracker, domain):
        SelectedCountry = tracker.get_slot("country")
        d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
        SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
        if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
            SelectedCountry = SelectedCountry[:-1]
        evisaForCountry_query = gf.get_query_for_travelbot('Find_onArrival',SelectedCountry)
        visa_values = gf.query_grakn(evisaForCountry_query)
        if (len(visa_values)>0):
            name = visa_values[0].get('name')
            address = visa_values[0].get('address')
            str =  "Μπορείς να εκδόσεις βίζα κατά την άφιξη. \n{0}".format(address)
            dispatcher.utter_message(str)
        return [] 

class AskForSlot2Action(Action):
    def name(self) -> Text:
        return "action_ask_answerVisa2"
    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        SelectedCountry = tracker.get_slot("country")
        d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
        SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
        if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
            SelectedCountry = SelectedCountry[:-1]
        mybuttons = []
        Channels_query = gf.get_query_for_travelbot('ChannelsTypeForCountry',SelectedCountry)
        answers = gf.query_grakn(Channels_query)
        myintent = "qVisa2"
        for row in answers:
          if (row.get('identifier') == "A0090"):
                entities_json = json.dumps({"answerVisa2": "A0090"})
                button_line = {"title": 'Ηλεκτρονική βίζας', "payload": f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
          if (row.get('identifier') == "A0091"):
                entities_json = json.dumps({"answerVisa2": "A0091"})
                button_line = {"title": 'Έκδοση στην Πρεσβεία', "payload": f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
          if (row.get('identifier') == "A0092"):
                entities_json = json.dumps({"answerVisa2": "A0092"})
                button_line = {"title": 'Έκδοση κατά την άφιξη', "payload": f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
        dispatcher.utter_message(text = "Ποιος φορέας έκδοσης σε ενδιαφέρει;", buttons = mybuttons)
        return []

class evidenceVisaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_evidence_visa_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> Optional[List[Text]]:

        Canconitnue = tracker.get_slot("evidence_visa")
        if (Canconitnue=="deny"): 
            custom_slots = ['evidence_visa']
        else:
            custom_slots = ['evidence_visa','answerVisa1','answerVisa2','answerVisa3',
            'answerVisa4','answerVisa5','answerVisa6','answerVisa7','answerVisa8']
        
            # Αν υπάρχει ένα κανάλι αφαιρώ την ερωτηση 2 για τους φορείς έκδοσης
            SelectedCountry = tracker.get_slot("country")
            d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
            SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
            if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
                SelectedCountry = SelectedCountry[:-1]
            Channels_query = gf.get_query_for_travelbot('ChannelsTypeForCountry',SelectedCountry)
            selectedChannel = ''
            channel = gf.query_grakn(Channels_query)
            if (len(channel)<=1):
                custom_slots.remove('answerVisa2')
            else:
                if (tracker.get_slot("answerVisa2") != None):
                    selectedChannel = tracker.get_slot("answerVisa2")
            if (selectedChannel =="All" or selectedChannel== ''):
                selectedChannel = "A0090|A0091|A0092"
                
            findchannels_query = gf.get_query_for_travelbot('evidence_answerForCountry',[SelectedCountry,selectedChannel])
            channelExcludeEvidence = gf.query_grakn(findchannels_query)
            answer1Remove= True
            answer3Remove= True
            answer4Remove= True
            answer5Remove= True
            answer6Remove= True
            answer7Remove= True
            answer8Remove= True

            for row in channelExcludeEvidence:
                if (row.get('identifier') == "A0031"):
                    answer1Remove = False
                if (row.get('identifier') == "A0033" or row.get('identifier') == "A0034"):
                    answer3Remove = False
                if (row.get('identifier') == "A0035" or row.get('identifier') == "A0036"):
                    answer4Remove = False              
                if (row.get('identifier') == "A0038"):
                    answer5Remove = False      
                if (row.get('identifier') == "A0039" or row.get('identifier') == "A0040"):
                    answer6Remove = False
                if (row.get('identifier') == "A0010" or row.get('identifier') == "A0011"):
                    answer8Remove = False
                if (row.get('identifier') == "A0005" or row.get('identifier') == "A0007" or row.get('identifier') == "A0008" or row.get('identifier') == "A0009"):
                    answer7Remove = False

            if answer1Remove:
                custom_slots.remove('answerVisa1')
            if answer3Remove:
                custom_slots.remove('answerVisa3')
            if answer4Remove:
                custom_slots.remove('answerVisa4')
            if answer5Remove:
                custom_slots.remove('answerVisa5')
            if answer6Remove:
                custom_slots.remove('answerVisa6')
            if answer7Remove:
                custom_slots.remove('answerVisa7')
            if answer8Remove:
                custom_slots.remove('answerVisa8')

        return custom_slots

class ActionDbVisaEvidence(Action):
    def name(self):
        return "action_db_evidence_visa"

    def run(self, dispatcher, tracker, domain):
        Canconitnue = tracker.get_slot("evidence_visa")
        if (Canconitnue!="deny"): 
            # Η επιλεγμένη χώρα
            SelectedCountry = tracker.get_slot("country")
            d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
            SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
            if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
                SelectedCountry = SelectedCountry[:-1]
            # Τα επιλεγμένα κανάλια
            selectedChannel = "A0090|A0091|A0092"
            if (tracker.get_slot("answerVisa2") != None and tracker.get_slot("answerVisa2")!="All"):
                selectedChannel = tracker.get_slot("answerVisa2")
            
            # Οι απαντήσεις για εξαίρεση δικαιολογητικών
            a1 = tracker.get_slot("answerVisa1") 
            a3 = tracker.get_slot("answerVisa3")
            a4 = tracker.get_slot("answerVisa4")
            a5 = tracker.get_slot("answerVisa5")
            a6 = tracker.get_slot("answerVisa6")
            a7 = tracker.get_slot("answerVisa7")
            if (a7 != None):
                if (a7 == "Yes"):
                    a7 = "A0006"
                else:
                    a7 = "A0005|A0007|A0008|A0009"

            a8 = tracker.get_slot("answerVisa8")
        
            # Τα δικαιολογητικά με βάση το κανάλι

            my_evidence_query = gf.get_query_for_travelbot('all_evidenceForCountryAndChannel',[SelectedCountry,selectedChannel])
            evidence = gf.query_grakn(my_evidence_query)

            # Εξαιρούνται τα δικαιολογητικά με βάση τις απαντήσεις
            
            answers = [a1,a3,a4,a5,a6,a7,a8]
            string_answers =  '|'.join(filter(None, answers))

            my_ex_evidence_query = gf.get_query_for_travelbot('Exclude_evidenceForCountryAndChannel',[SelectedCountry,selectedChannel,string_answers])
            EvidenceExclude = gf.query_grakn(my_ex_evidence_query)

            evidence_list = gf.find_list_diff(evidence,EvidenceExclude)
            
            if (len(evidence_list)>0):
                str_data = "🗨 Τα δικαιολογητικά 📄 που απαιτούνται είναι τα εξής: \n"      
                for evidence in evidence_list:
                    str_data += f"- {evidence.get('name')}." + "\n"
                    str_data += evidence.get('description') + "\n"
            else:
                str_data = "Δεν γνωρίζω λεπτομέρειες για την επιλεγμένη χώρα."
        
            dispatcher.utter_message(str_data)
        return[]

class CostVisaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_cost_visa_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> Optional[List[Text]]:

        Canconitnue = tracker.get_slot("cost_visa")
        if (Canconitnue=="deny"): 
            custom_slots = ['cost_visa']
        else:
            custom_slots = ['cost_visa','answerVisa14','answerVisa10','answerVisa13','answerVisa9','answerVisa15','answerVisa16','answerVisa17']
            SelectedCountry = tracker.get_slot("country")
            d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
            SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
            if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
                SelectedCountry = SelectedCountry[:-1]

            Channels_query = gf.get_query_for_travelbot('ChannelsTypeForCountry',SelectedCountry)
            channel = gf.query_grakn(Channels_query)
    
            cost_query = gf.get_query_for_travelbot('AnswersOfCostForCountry',SelectedCountry)
            answers = gf.query_grakn(cost_query)
            answer9Remove= True
            answer10Remove= True
            answer16Remove= True
            answer17Remove= True
            answer13Remove= True
            answer14Remove= True
            answer15Remove= True
            for row in answers:
                if (row.get('identifier') >= "A0041" and row.get('identifier') <= "A0048"):
                    answer9Remove = False
                if (row.get('identifier') == "A0049" or row.get('identifier') == "A0050"):
                    answer10Remove = False
                if (row.get('identifier') == "A0051" or row.get('identifier') == "A0052" or row.get('identifier') == "A0053"):
                    answer16Remove = False
                if (row.get('identifier') == "A0054" or row.get('identifier') == "A0055"):
                    answer17Remove = False
                if (row.get('identifier') == "A0090" or row.get('identifier') == "A0091"  or row.get('identifier') == "A0092"):
                    answer13Remove = False
                if (row.get('identifier') == "A0039" or row.get('identifier') == "A0040"):
                    answer14Remove = False
                if (row.get('identifier') == "A0010" or row.get('identifier') == "A0011"):
                    answer15Remove = False

            transit = tracker.get_slot("answerVisa14")
            if transit == "A0040":
                answer10Remove = True
                answer9Remove = True
                answer13Remove = True
    
            if answer9Remove:
                custom_slots.remove('answerVisa9')
            if answer10Remove:
                custom_slots.remove('answerVisa10')
            if answer16Remove:
                custom_slots.remove('answerVisa16')
            if answer17Remove:
                custom_slots.remove('answerVisa17')
            if answer13Remove or (len(channel)<=1):
                custom_slots.remove('answerVisa13')
            if answer14Remove:
                custom_slots.remove('answerVisa14')
            if answer15Remove:
                custom_slots.remove('answerVisa15')
        return custom_slots       

class AskForΑnswerVisa9Action(Action):
    def name(self) -> Text:
        return "action_ask_answerVisa9"
    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        SelectedCountry = tracker.get_slot("country")
        d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
        SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
        if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
            SelectedCountry = SelectedCountry[:-1]
        mybuttons = []
        cost_query = gf.get_query_for_travelbot('AnswersOfCostForCountry',SelectedCountry)
        answers = gf.query_grakn(cost_query)
        myintent = "qVisa9"
        for row in answers:
            if (row.get('identifier') == "A0041"):
                entities_json = json.dumps({"answerVisa9": "A0041"})
                button_line = {"title": 'Διάρκεια Μέχρι 15 ημέρες', "payload": f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
            if (row.get('identifier') == "A0042"):
                entities_json = json.dumps({"answerVisa9": "A0042"})
                button_line = {'title': 'Διάρκεια Μέχρι 16 ημέρες' ,'payload': f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
            if (row.get('identifier') == "A0043"):
                entities_json = json.dumps({"answerVisa9": "A0043"})
                button_line = {'title': 'Διάρκεια Μέχρι 1 μήνα' ,'payload': f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
            if (row.get('identifier') == "A0044"):
                entities_json = json.dumps({"answerVisa9": "A0044"})
                button_line = {'title': 'Διάρκεια Μέχρι 2 μήνες' ,'payload': f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
            if (row.get('identifier') == "A0045"):
                entities_json = json.dumps({"answerVisa9": "A0045"})
                button_line = {'title': 'Διάρκεια Μέχρι 3 μήνες' ,'payload': f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
            if (row.get('identifier') == "A0046"):
                entities_json = json.dumps({"answerVisa9": "A0046"})
                button_line = {'title': 'Διάρκεια Μέχρι 6 μήνες' ,'payload': f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
            if (row.get('identifier') == "A0047"):
                entities_json = json.dumps({"answerVisa9": "A0047"})
                button_line = {'title': 'Διάρκεια Μέχρι 1 έτος' ,'payload': f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
            if (row.get('identifier') == "A0048"):
                entities_json = json.dumps({"answerVisa9": "A0048"})
                button_line = {'title': 'Διάρκεια Πάνω από 1 έτος' ,'payload': f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)

        dispatcher.utter_message(text = "Ποια είναι η διάρκεια του ταξιδιού σου;", buttons = mybuttons)
        return []

class AskForSlot13Action(Action):
    def name(self) -> Text:
        return "action_ask_answerVisa13"
    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        SelectedCountry = tracker.get_slot("country")
        d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
        SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
        if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
            SelectedCountry = SelectedCountry[:-1]
        mybuttons = []
        cost_query = gf.get_query_for_travelbot('AnswersOfCostForCountry',SelectedCountry)
        answers = gf.query_grakn(cost_query)
        myintent = "qVisa13"
        for row in answers:
          if (row.get('identifier') == "A0090"):
                entities_json = json.dumps({"answerVisa13": "A0090"})
                button_line = {"title": 'Ηλεκτρονική βίζας', "payload": f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
          if (row.get('identifier') == "A0091"):
                entities_json = json.dumps({"answerVisa13": "A0091"})
                button_line = {"title": 'Έκδοση στην Πρεσβεία', "payload": f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
          if (row.get('identifier') == "A0092"):
                entities_json = json.dumps({"answerVisa13": "A0092"})
                button_line = {"title": 'Έκδοση κατά την άφιξη', "payload": f"/{myintent}{entities_json}"}
                mybuttons.append(button_line)
        dispatcher.utter_message(text = "Ποιος φορέας έκδοσης σε ενδιαφέρει;", buttons = mybuttons)
        return []

class ActionDbVisaCost(Action):
    def name(self):
        return "action_db_cost_visa"

    def run(self, dispatcher, tracker, domain):

        # Η επιλεγμένη χώρα
        Canconitnue = tracker.get_slot("cost_visa")
        if (Canconitnue!="deny"):
            SelectedCountry = tracker.get_slot("country")
            d = {ord('\N{COMBINING ACUTE ACCENT}'):None}
            SelectedCountry = ud.normalize('NFD',SelectedCountry).upper().translate(d)
            if SelectedCountry.endswith('Σ') or SelectedCountry.endswith('Υ'):
                SelectedCountry = SelectedCountry[:-1]
            a9 = tracker.get_slot("answerVisa9") 
            a10 = tracker.get_slot("answerVisa10")
            a16 = tracker.get_slot("answerVisa16")
            a17 = tracker.get_slot("answerVisa17")
            a13 = tracker.get_slot("answerVisa13")
            a14 = tracker.get_slot("answerVisa14")
            a15 = tracker.get_slot("answerVisa15")
            if a14=="A0040":  
                a13 = None
            cost = []
            answers = [a13,a14,a9,a10,a15,a16,a17]

            for answer in answers:
                if (len(cost)!=1):
                    if (answer != None):
                        cost_query = gf.get_query_for_travelbot('CostForCountryID',[SelectedCountry,answer])
                        costAnswer = gf.query_grakn(cost_query)
                        if (len(costAnswer)!=0):
                            if (len(cost)!=0):
                                cost = gf.find_list_common(cost,costAnswer)
                            else:
                                cost = costAnswer

            if (len(cost)>0):
                str_data ="Το κόστος για την έκδοση "
                for costLine in cost:
                    cost_query = gf.get_query_for_travelbot('CostForID',costLine.get('identifier'))
                    costResult = gf.query_grakn(cost_query) 
                    thiscost = costResult[0]
                    currency = thiscost.get('currency').replace("EUR","ευρώ").replace("USD","δολάρια")
                    str_data += thiscost.get('description') + " είναι : \n"
                    str_data += thiscost.get('cost_value') + " " + currency  + "\n"
            else:
                str_data = "Λυπάμαι! Δεν μπόρεσα να εντοπίσω το κόστος."

            dispatcher.utter_message(str_data)
        return[]


class ActionDbDurationEkaa(Action):
    def name(self):
        return "action_db_Duration_Ekaa"
        
    def run(self, dispatcher, tracker, domain):
        my_ekaaDuration_query = gf.get_query_for_travelbot('Duration_ekaa','')
        descriptions = gf.query_grakn(my_ekaaDuration_query)
        str_data = ""
        for descr in descriptions:
            str_data += descr.get('category')
    
        dispatcher.utter_message(str_data)
        return [] 


class ActionDbPlaceOfSubmissionLocation(Action):	
#       Εντοπισμός γραφείου διαβατηρίων
#       Εξαγωγή λέξεων από το String - έως 3 λέξεις
#       Αφαίρεση τελευταίου χαρακτήρα από τις εισαχθέντες λέξεις
#       Διερεύνιση σε 4 πεδία - areaServed, location, Title, Address
#       Εμφάνιση των στοιχείων σε carousel
    def name(self):
        return "action_db_Place_Of_Submission_location"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        db = mysql.connector.connect(**config)        
        
        nameoflocation = tracker.get_slot("location")

        if not nameoflocation:
            nameoflocation1 =  'ωωωωωωωωω'    # Περίπτωση να ζητηθεί αναζήτηση με κενή φράση. Προκειμένου να μην εμφανιστούν 
            nameoflocation2 =  ''             # όλα τα contact points θέτω στην 1η λέξη 'ωωωωωωωωωωωω', οπότε δεν θα επιστρέψει
            nameoflocation3 =  ''             # γραφεία διαβατηρίων
        else:
            words = nameoflocation.split()
            len_words = len(words)

            if len_words == 1:
               nameoflocation1 =  words[0]
               nameoflocation2 =  ''
               nameoflocation3 =  ''
            elif len_words == 2:
               nameoflocation1 =  words[0]
               nameoflocation2 =  words[1]
               nameoflocation3 =  ''
            else:
               nameoflocation1 =  words[0]
               nameoflocation2 =  words[1]
               nameoflocation3 =  words[2]       

            temp = nameoflocation1
            lenx = len(temp)
            nameoflocation1 = (temp[0:lenx-1:1])

            temp = nameoflocation2
            lenx = len(temp)
            nameoflocation2 = (temp[0:lenx-1:1])

            temp = nameoflocation3
            lenx = len(temp)
            nameoflocation3 = (temp[0:lenx-1:1])
                                    
        q = "select * from contactpoint as cp, publicservice_contactpoint as ps_cp where ps_cp.identifier_ps = '{3}' and ps_cp.identifier_cp = cp.identifier and ((cp.areaserved like '%{0}%' and cp.areaserved like '%{1}%' and cp.areaserved like '%{2}%') or (cp.location like '%{0}%' and cp.location like '%{1}%' and cp.location like '%{2}%') or (cp.title like '%{0}%' and cp.title like '%{1}%' and cp.title like '%{2}%') or (cp.address like '%{0}%' and cp.address like '%{1}%' and cp.address like '%{2}%')) order by title".format(nameoflocation1,nameoflocation2,nameoflocation3,IDENTIFIER_PS_PASSPORT)

        email_subject = "TravelDocBot - ΓΡΑΦΕΙΑ ΕΚΔΟΣΗΣ ΔΙΑΒΑΤΗΡΙΩΝ ΓΙΑ ΠΕΡΙΟΧΗ/ΔΗΜΟ ΚΑΤΟΙΚΙΑΣ: {}".format(nameoflocation)
        email_results = ''
        json_data_list = []
        img_url_point = "https://cdn.pixabay.com/photo/2013/07/12/13/53/police-officer-147501_960_720.png"
        
        cursor = db.cursor()
        
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            i = 0
            len_data = len(results)
            for row in results:
                i+=1
                # Εμφάνιση των στοιχείων (έως 5) και ετοιμασία για email (όλα)
                title = row[1]
                address = row[2]
                location = row[3]   
                area = row[4]
                hours = row[5]
                Email = row[6]
                Tel = row[7]
                addr = ''
                addr = GOOGLE_MAP_ADDRESS + address.replace(" ","+")
                str_data_aa     = "{}. Υπηρεσία:".format(i)
                str_data        = "{},\nΔιεύθυνση: {},\nΠεριοχή: {},\nΕδαφική αρμοδιότητα: {},\nΩράριο Εξυπηρέτησης: {},\nE-mail: {},\nΤηλέφωνο: {}".format(title,address,location,area,hours,Email,Tel)
                str_data_email  = "{}.Υπηρεσία: {}\nΔιεύθυνση: {}\nΠεριοχή: {}\nΕδαφική αρμοδιότητα: {}\nΩράριο Εξυπηρέτησης: {}\nE-mail: {}\nΤηλέφωνο: {}\nΓια εμφάνιση στο χάρτη πάτησε ({}).\n".format(i,title,address,location,area,hours,Email,Tel, addr)
                elem = {
                    "title": str_data_aa,
                    "subtitle": str_data,
                    "image_url": img_url_point,
                    "buttons": [{
                        "title": "Εμφάνιση στο χάρτη",
                        "url": addr,
                        "type": "web_url"
                    }]
                }                               
                if i == 1:
                   response = """Το/τα γραφεία έκδοσης διαβατηρίων που εντοπίστηκαν για την περιοχή {} είναι {} : \n""".format(nameoflocation, len_data)
                   dispatcher.utter_message(response)
                   email_results = response
                email_results = email_results + "\n" + str_data_email
                if i <= 5:
                   json_data_list.append(elem)                
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν γραφεία διαβατηρίων... Μπορείς να δεις και [εδώ](http://www.passport.gov.gr/grafeia-kai-orario/grafeia-diavatirion-ellada/)")
            elif len_data > 5:
                dispatcher.utter_message("Εμφανίστηκαν 5 από {} αποτελέσματα.\nΜπορείς να επαναδιατυπώσεις την περιοχή σου για περιορισμό των αποτελεσμάτων".format(len_data))
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()       

        if results:
            dsp_carousel = {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": json_data_list                        
                }
            }
            dispatcher.utter_message(attachment=dsp_carousel)


        return[SlotSet("info_for_email", email_results), SlotSet("subject_for_email", email_subject)]    
       

class SendAnEmail(Action):
#       Αποστολή email 

    def name(self) -> Text:
        return "action_send_email"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        email_text      = format(tracker.get_slot("info_for_email"))
        subject         = format(tracker.get_slot("subject_for_email"))

        if not email_text:
            dispatcher.utter_message("Φαίνεται ότι δεν υπάρχουν στοιχεία για αποστολή! 😢 Λυπάμαι αλλά η αποστολή ακυρώνεται... ")
            return[]
            
        port =  465
        smtp_server = "smtp.gmail.com"
        login = LOGIN_EMAIL    # paste your login generated by Gmail
        password = PASSWORD    # paste your password generated by Gmail
        sender_email = SENDER_EMAIL
        receiver_email = tracker.get_slot("email")

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = receiver_email
        # Write the plain text part

        text = "Γειά σου!\nΠαρακάτω μπορείς να βρεις τις πληροφορίες που ζήτησες.\n\n"
        text = text + email_text + "\n\nPassBot.\nThe Greek Virtual Passport Agent.\n\n\n\nΑυτόματο email - ΠΑΡΑΚΑΛΩ ΜΗΝ ΑΠΑΝΤΗΣΕΙΣ"
        
        part1 = MIMEText(text, "plain")
        message.attach(part1)

        context = ssl.create_default_context()

        # send the email
        dispatcher.utter_message ("Αποστολή email σε {}".format(receiver_email))
        
        try:
          with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(login, password)
            server.sendmail( sender_email, receiver_email, message.as_string() )
        except smtplib.SMTPAuthenticationError:
          dispatcher.utter_message('Αδυναμία σύνδεσης με mail Server. Username and Password not accepted...')
        #  except (gaierror, ConnectionRefusedError):
        #    dispatcher.utter_message('Αδυναμία σύνδεσης με mail Server. Bad connection settings...')
        except smtplib.SMTPServerDisconnected:
          dispatcher.utter_message('Αδυναμία σύνδεσης με mail Server. Disconnected...')          
        except smtplib.SMTPException as e:
          dispatcher.utter_message('Αδυναμία σύνδεσης με mail Server. ' + str(e))
        else:
          dispatcher.utter_message('Η αποστολή του email ολοκληρώθηκε.')
        
        return[AllSlotsReset()]

class ActionDbPlaceOfSubmission(Action):	
#       Τόπος υποβολής των δικαιολογητικών
#       Ανάκτηση και εμφάνιση Sort_Description από table "rule" για PS = "Ps0001" και rule.name = 'PLACE OF SUBMISSION OF DOCUMENTS'.
    def name(self):
        return "action_db_Place_Of_Submission"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)

        cursor = db.cursor()
        q = "select rule.sort_description from publicservice_rule as ps_rule, rule where ps_rule.identifier_ps = '{}' and ps_rule.identifier_ru = rule.identifier and rule.name = 'PLACE OF SUBMISSION OF DOCUMENTS'".format(IDENTIFIER_PS_PASSPORT)

        response = """Τα δικαιολογητικά για την έκδοση διαβατηρίου, υποβάλλονται : """
        dispatcher.utter_message(response)
        
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                descr = row[0]
                dispatcher.utter_message(format(descr))
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()
        
        return []      

class EvidenceForm(FormValidationAction):
#   Φόρμα για τις 12 ερωτήσεις εξαγωγής των εξατομικευμένων δικαιολογητικών

    def name(self) -> Text:
        return "validate_evidence_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> Optional[List[Text]]:

        """A list of required slots that the form has to fill"""

        # custom_slots: είναι το σύνολο των slots που πρέπει να συμπληρώσει 
        # ο χρήστης, οι ερωτήσεις 5,11,12 γίνονται υπό προυποθέσεις,
        # στους παρακάτω ελέγχους if αφαιρούντε τα slots για τις ερωτήσεις 
        # που δεν χρειάζεται να απαντηθούν

        custom_slots = [ 'answer' + str(i) for i in range(1,13)]

        a1 = tracker.get_slot("answer1")
        a2 = tracker.get_slot("answer2")

        # Περίπτωση Αρχικής έκδοσης/Ανανέωσης/Αντικατάστασης - Ενήλικος 
        # == αποκλεισμός ερώτησης 12-κατ'εξαίρεση έκδοσης μετά από απώλεια-κλοπή
        if (a1 == 'A0001' or a1 == 'A0002' or a1 == 'A0003') and (a2 == 'A0005'):
            custom_slots.remove('answer12')

            return custom_slots
        # Περίπτωση Αρχικής έκδοσης/Ανανέωσης/Αντικατάστασης - <12 
        # == αποκλεισμός ερωτήσεων 5-δακτυλικά αποτυπώματα, 10-ανυπότακτος εξωτερικού, 12-κατ'εξαίρεση έκδοσης μετά από απώλεια-κλοπή
        elif (a1 == 'A0001' or a1 == 'A0002' or a1 == 'A0003') and (a2 == 'A0006') :
            custom_slots.remove('answer5')
            custom_slots.remove('answer10')
            custom_slots.remove('answer12')

            return custom_slots
        # Περίπτωση Αρχικής έκδοσης/Ανανέωσης/Αντικατάστασης - =12 και 13-14 και >14 ετών 
        # == αποκλεισμός ερωτήσεων 10-ανυπότακτος εξωτερικού, 12-κατ'εξαίρεση έκδοσης μετά από απώλεια-κλοπή
        elif (a1 == 'A0001' or a1 == 'A0002' or a1 == 'A0003') and (a2 == 'A0007' or a2 == 'A0008' or a2 == 'A0009') : 
            custom_slots.remove('answer10')
            custom_slots.remove('answer12') 

            return  custom_slots
        # Περίπτωση Απώλειας/κλοπής - <12 
        # == αποκλεισμός ερωτήσεων 5-δακτυλικά αποτυπώματα, 10-ανυπότακτος εξωτερικού
        elif (a1 == 'A0004') and (a2 == 'A0006') :
            custom_slots.remove('answer5')
            custom_slots.remove('answer10')  

            return slots_mapped_in_domain + custom_slots
        # Περίπτωση Απώλειας/κλοπής - =12 και 13-14 και >14 ετών 
        # == αποκλεισμός ερώτησης 10-ανυπότακτος εξωτερικού
        elif (a1 == 'A0004') and (a2 == 'A0007' or a2 == 'A0008' or a2 == 'A0009') :
            custom_slots.remove('answer10')

            return  custom_slots
        # Περίπτωση Απώλειας/κλοπής - Ενήλικος == ισχύουν όλες οι ερωτήσεις
        else:
            return custom_slots

    async def extract_answer5(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:

        answer4 = tracker.get_slot("answer4")
        answer5 = tracker.get_slot("answer5")

        print('intent : ', tracker.latest_message['intent'].get('name') )

        if answer4 and not answer5:
            dispatcher.utter_message(template="utter_ask_answer5")
            return {}
        else:
            return{"answer5": answer5}


    async def extract_answer10(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:

        answer9 = tracker.get_slot("answer9")
        answer10 = tracker.get_slot("answer10")

        print('intent : ',tracker.latest_message['intent'].get('name') )
        if answer9 and not answer10:
            dispatcher.utter_message(template="utter_ask_answer10")
            return {}
        else:
            return{"answer10": answer10}

    async def extract_answer12(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:

        answer11 = tracker.get_slot("answer11")
        answer12 = tracker.get_slot("answer12")

        print('intent : ', tracker.latest_message['intent'].get('name') )

        if answer11 and not answer12:
            dispatcher.utter_message(template="utter_ask_answer12")
            return {}
        else:
            return{"answer12": answer12}  

class ActionDbEvidence(Action):	
#       Εξατομικευμένα δικαιολογητικά
#       Ανάκτηση περιγραφών απαντήσεων που έχουν δοθεί, από table "AnswerForDoc". Απαιτείται μόνο για το email.
#       Ανάκτηση δικαιολογητικών βάσει των απαντήσεων, από table "evidence". Εμφάνιση name. Email name, description.
#       Ανάκτηση κόστους βάσει των απαντήσεων, από table "cost". Εμφάνιση αξίας, νομίσματος, sort_description. Email αξία νόμισμα, description.
#       Ανάκτηση εξόδου βάσει των απαντήσεων, από table "output". Εμφάνιση name. Email name , description.
    def name(self):
        return "action_db_evidence"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)        

        a1 = tracker.get_slot("answer1")
        a2 = tracker.get_slot("answer2")
        a3 = tracker.get_slot("answer3")
        a4 = tracker.get_slot("answer4")
        a5 = tracker.get_slot("answer5")
        a6 = tracker.get_slot("answer6")
        a7 = tracker.get_slot("answer7")
        a8 = tracker.get_slot("answer8")
        a9 = tracker.get_slot("answer9")
        a10 = tracker.get_slot("answer10")
        a11 = tracker.get_slot("answer11")
        a12 = tracker.get_slot("answer12")

        
        
        str_data = "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12)

        
        # Ενημέρωση περιεχομένου με 'Όχι' στις απαντήσεις των ερωτήσεων που τυχόν εξαιρέθηκαν (5-10-12) για εξαγωγή των ορθών δικαιολογητικών
        if a5 == None:
           a5 = 'A0014'
        if a10 == None:
           a10 = 'A0026'
        if a12 == None:
           a12 = 'A0030'   

        ### grakn query code     ###
        email_subject = "TravelDocBot - ΕΞΑΤΟΜΙΚΕΥΜΕΝΑ ΔΙΚΑΙΟΛΟΓΗΤΙΚΑ ΠΟΥ ΑΠΑΙΤΟΥΝΤΑΙ ΓΙΑ ΕΚΔΟΣΗ ΔΙΑΒΑΤΗΡΙΟΥ"
        str_data_email = ''

        answers = [a1,a2,a3,a4,a5,a6,a7,a8,a9,a10,a11,a12]
        string_answers = '(' + '|'.join(answers) + ')'

        my_cost_query = gf.get_query_string('cost_query',string_answers)
        grakn_values = gf.query_grakn(my_cost_query)
        print(grakn_values)

        cost = grakn_values[0]
        str_data = f"🗨 Θα κοστίσει {cost.get('cost_value')} {cost.get('currency')}.\n {cost.get('sort_description')}.\n"
        str_data_email = str_data
        
        dispatcher.utter_message(str_data)

        my_output_query = gf.get_query_string('output_query',string_answers)
        output_grakn_values = gf.query_grakn(my_output_query)
        passport_name = output_grakn_values[0]
        print(output_grakn_values)

        str_data = f"🗨 To διαβατήριο που θα εκδοθεί για την περίπτωσή σου είναι {passport_name.get('name')}."
        str_data_email += f"🗨 To διαβατήριο που θα εκδοθεί για την περίπτωσή σου είναι {passport_name.get('name')}.\n"
        
        dispatcher.utter_message(str_data)

        my_ex_evidence_query = gf.get_query_string('excluded_evidence',string_answers)
        ex_evidence_grakn_values = gf.query_grakn(my_ex_evidence_query)

        my_evidence_query = gf.get_query_string('all_evidence',string_answers)
        evidence_grakn_values = gf.query_grakn(my_evidence_query)
        
        evidence_list = gf.find_list_diff(evidence_grakn_values,ex_evidence_grakn_values)
        print(evidence_list)

        str_data        = "🗨 Τα δικαιολογητικά 📄 που απαιτούνται είναι τα εξής: \n"
        str_data_email += str_data

        for evidence in evidence_list:
            str_data += f"- {evidence.get('name')}.\n"
            str_data_email  += f"- {evidence.get('name')}.\n"
        
        dispatcher.utter_message(str_data)
        ### grakn query code end ###

       
        response = """😃 Ευχαριστώ για το χρόνο σου..."""
        dispatcher.utter_message(response)        
               
    
        # Ερώτηση για αποστολή mail, εφόσον εμφανίστηκαν στοιχεία 
        if not str_data_email:
            dispatcher.utter_message(template="utter_anything_else")            
        else:
            message = "Θα ήθελες να σου στείλω με 📧 email τις πληροφορίες εμπλουτισμένες;"
            buttons = [{'title': BUTTON_YES, 
                        'payload': '/affirm'}, 
                        {'title': BUTTON_NO, 
                        'payload': '/deny'}] 

        return[SlotSet("info_for_email", str_data_email), SlotSet("subject_for_email", email_subject)]


class ActionDbSundayΟffice(Action):	
#       Γραφεία ανοιχτά την Κυριακή / Εμφάνιση των στοιχείων σε carousel

    def name(self):
        return "action_db_Sunday_office"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        db = mysql.connector.connect(**config)        
            
        q = "select * from contactpoint as cp, publicservice_contactpoint as ps_cp where ps_cp.identifier_ps = '{}' and ps_cp.identifier_cp = cp.identifier and (hoursavailable like '%ΚΥ%' or hoursavailable like '%ΚΥΡΙΑΚΗ%' or hoursavailable like '%κυριακή%' or hoursavailable like '%Sunday%') order by title".format(IDENTIFIER_PS_PASSPORT)
        
        cursor = db.cursor()

        email_subject = "TravelDocBot - ΓΡΑΦΕΙΑ ΕΚΔΟΣΗΣ ΔΙΑΒΑΤΗΡΙΩΝ ΑΝΟΙΚΤΑ ΤΗΝ ΚΥΡΙΑΚΗ "
        email_results = ''
        json_data_list = []
        img_url_point = "https://cdn.pixabay.com/photo/2013/07/12/13/53/police-officer-147501_960_720.png"        
        
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            i = 0
            len_data = len(results)
            for row in results:
                i+=1
                # Εμφάνιση των στοιχείων (έως 5) και ετοιμασία για email (όλα)
                title = row[1]
                address = row[2]
                location = row[3]   
                area = row[4]
                hours = row[5]
                Email = row[6]
                Tel = row[7]
                addr = ''
                addr = GOOGLE_MAP_ADDRESS + address.replace(" ","+")
                str_data_aa     = "{}. Υπηρεσία:".format(i)
                str_data        = "{},\nΔιεύθυνση: {},\nΠεριοχή: {},\nΕδαφική αρμοδιότητα: {},\nΩράριο Εξυπηρέτησης: {},\nE-mail: {},\nΤηλέφωνο: {}".format(title,address,location,area,hours,Email,Tel)
                str_data_email  = "{}.Υπηρεσία: {}\nΔιεύθυνση: {}\nΠεριοχή: {}\nΕδαφική αρμοδιότητα: {}\nΩράριο Εξυπηρέτησης: {}\nE-mail: {}\nΤηλέφωνο: {}\nΓια εμφάνιση στο χάρτη πάτησε ({}).\n".format(i,title,address,location,area,hours,Email,Tel, addr)
                elem = {
                    "title": str_data_aa,
                    "subtitle": str_data,
                    "image_url": img_url_point,
                    "buttons": [{
                        "title": "Εμφάνιση στο χάρτη",
                        "url": addr,
                        "type": "web_url"
                    }]
                }
                if i == 1:
                   response = """Το/τα γραφεία έκδοσης διαβατηρίων που εντοπίστηκαν, σε όλη την Ελλάδα, ανοιχτά την Κυριακή, είναι {} : \n""".format(len_data)        
                   dispatcher.utter_message(response)
                   email_results = response
                email_results = email_results + "\n" + str_data_email
                if i <= 5:
                   json_data_list.append(elem)
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν γραφεία διαβατηρίων... Εναλλακτικά εναλλακτικά μπορείς να ψάξεις και [εδώ](http://www.passport.gov.gr/grafeia-kai-orario/grafeia-diavatirion-ellada/)")
            elif len_data > 5:
                dispatcher.utter_message("Εμφανίστηκαν 5 από {} αποτελέσματα.".format(len_data))
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()

        if results:
            dsp_carousel = {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": json_data_list                        
                }
            }
            dispatcher.utter_message(attachment=dsp_carousel)

        return[SlotSet("info_for_email", email_results), SlotSet("subject_for_email", email_subject)]

class ActionDbCriterionRequirement(Action):	
#       Προυποθέσεις έκδοσης διαβατηρίου
#       Ανάκτηση και εμφάνιση Sort_Description (Description για email) από table "CriterionRequirement" για PS = "Ps0001"
    def name(self):
        return "action_db_CriterionRequirement"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)
        
        cursor = db.cursor()
        q = "select cr.description, cr.sort_description from publicservice_criterionrequirement as ps_cr, criterionrequirement as cr where ps_cr.identifier_ps = '{}' and ps_cr.identifier_cr = cr.identifier".format(IDENTIFIER_PS_PASSPORT)
        
        email_subject = "TravelDocBot - ΠΡΟΥΠΟΘΕΣΕΙΣ ΕΚΔΟΣΗΣ ΔΙΑΒΑΤΗΡΙΟΥ"
        email_results = ''
        
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            i = 0
            for row in results:
                i+=1
                descr = row[0]
                sort_descr = row[1]
                if i == 1:                                                       
                    response = """Οι προϋποθέσεις έκδοσης διαβατηρίου είναι οι εξής : """
                    dispatcher.utter_message(response)
                    response = """Οι λεπτομερείς προϋποθέσεις έκδοσης διαβατηρίου είναι οι εξής : """
                    email_results = response
                dispatcher.utter_message(format(sort_descr))
                email_results = email_results + "\n\n" + format(descr)
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()

        return[SlotSet("info_for_email", email_results), SlotSet("subject_for_email", email_subject)]

class ActionDbCasesOfPassportIssue(Action):	
#       Περιπτώσεις έκδοσης διαβατηρίου
#       Ανάκτηση και εμφάνιση Sort_Description από table "rule" για PS = "Ps0001" και rule.name = 'CASES OF PASSPORT ISSUE'.
    def name(self):
        return "action_db_cases_of_passport_issue"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)    
        
        cursor = db.cursor()
        q = "select rule.sort_description from publicservice_rule as ps_rule, rule where ps_rule.identifier_ps = '{}' and ps_rule.identifier_ru = rule.identifier and rule.name = 'CASES OF PASSPORT ISSUE'".format(IDENTIFIER_PS_PASSPORT)

        response = """Οι περιπτώσεις έκδοσης διαβατηρίου είναι οι εξής : """
        dispatcher.utter_message(response)
        
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                descr = row[0]
                dispatcher.utter_message(format(descr))
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()
        
        return [] 

class ActionDPassportIssueProcedure(Action):	
#       Διαδικασία έκδοσης διαβατηρίου
#       Ανάκτηση και εμφάνιση Sort_Description (Description για email) από table "rule" για PS = "Ps0001" και rule.name = 'PASSPORT ISSUE PROCEDURE'.
    def name(self):
        return "action_db_passport_issue_procedure"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)    
        
        cursor = db.cursor()
        q = "select rule.description, rule.sort_description from publicservice_rule as ps_rule, rule where ps_rule.identifier_ps = '{}' and ps_rule.identifier_ru = rule.identifier and rule.name = 'PASSPORT ISSUE PROCEDURE'".format(IDENTIFIER_PS_PASSPORT)

        email_subject = "PassBot - ΔΙΑΔΙΚΑΣΙΑ ΕΚΔΟΣΗΣ ΔΙΑΒΑΤΗΡΙΟΥ"
        email_results = ''
        
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            i = 0
            for row in results:
                i+=1
                descr = row[0]
                sort_descr = row[1]
                if i == 1:                                                       
                    response = """Η διαδικασία που ακολουθείται από την υποβολή των δικαιολογητικών μέχρι και την παραλαβή του νέου διαβατηρίου είναι η εξής : """
                    dispatcher.utter_message(response)                
                    email_results = response
                dispatcher.utter_message(format(sort_descr))
                email_results = email_results + "\n\n" + format(descr)
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()

        return[SlotSet("info_for_email", email_results), SlotSet("subject_for_email", email_subject)]   

class ActionDbListOfEvidence(Action):	
#       Λίστα των πιθανών δικαιολογητικών
#       Ανάκτηση και εμφάνιση ev.name από table "evidence" για PS = "Ps0001".
    def name(self):
        return "action_db_list_of_evidence"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)            

        response = """Τα πιθανά δικαιολογητικά 🧾 που μπορεί να ζητηθούν για τη έκδοση διαβατηρίου είναι τα εξής (αναλόγως την περίπτωση):"""
        dispatcher.utter_message(response)        

        cursor = db.cursor()
        q = "select distinct ev.name from evidence as ev, publicservice_evidence as ps_ev where ps_ev.identifier_ps = '{}' and ps_ev.identifier_ev = ev.identifier".format(IDENTIFIER_PS_PASSPORT)
       
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            str_data = ''
            for row in results:
                descr = row[0]
                str_data = str_data + "- {}.\n".format(descr)                
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα δικαιολογητικά...")
            else:
                dispatcher.utter_message(str_data)
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()
        
        return []

class ActionDbCost(Action):	
#       Κόστος έκδοσης διαβατηρίου
#       Ανάκτηση δεδομένων από table "cost" για PS = Ps0001
    def name(self):
        return "action_db_cost"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)
       
       
        cursor = db.cursor()
        q = "select cost.value, cvcurrency.name, cost.sort_description from publicservice_cost as ps_cost, cost, cvcurrency where ps_cost.identifier_ps = '{}' and ps_cost.identifier_cost = cost.identifier and cost.currency = cvcurrency.code".format(IDENTIFIER_PS_PASSPORT)
        
        response = """Το κόστος έκδοσης διαβατηρίου εξαρτάται από την περίπτωση έκδοσης, την ηλικία του ενδιαφερομένου και ειδικές συνθήκες που ίσως υπάρχουν. Έτσι διαμορφώνεται ως εξής : """
        dispatcher.utter_message(response)
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                costvalue = row[0]
                curname = row[1]
                costdescr = row[2]
                details = ('Κόστος: {0} {1}. - {2}'.format(costvalue, curname, costdescr))
                dispatcher.utter_message(format(details))
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
            else:
                response = """Για την πληρωμή του κόστους εφαρμόζεται η διαδικασία είσπραξης του ηλεκτρονικού παραβόλου [e-paravolo](http://www.passport.gov.gr/diadikasia-ekdosis/documents/eparavolo.html)."""
                dispatcher.utter_message(response)
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()
        
        return []

class ActionDbAbout(Action):	
#       Περί διαβατηρίου
#       Ανάκτηση και εμφάνιση Description από table "publicService" για PS = "Ps0001" .
    def name(self):
        return "action_db_about"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)
        
        cursor = db.cursor()
        q = "select description from publicservice where identifier = '{}'".format(IDENTIFIER_PS_PASSPORT)
        q1 = "select ch_type.description from publicservice as ps, channel as ch, publicservice_channel as ps_ch, cvchanneltype as ch_type where ps.identifier = '{}' and ps.identifier = ps_ch.identifier_ps and ps_ch.identifier_ch = ch.identifier and ch.type = ch_type.code".format(IDENTIFIER_PS_PASSPORT)
             
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                descr = row[0]
                dispatcher.utter_message(format(descr))
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
            else:
                response = """Η υπηρεσία της έκδοσης διαβατηρίου παρέχεται υπό προϋποθέσεις από τα εξής κανάλια : """
                dispatcher.utter_message(response)
                cursor.execute(q1)
                results = cursor.fetchall()
                str_data = ''
                for row in results:
                    descr = row[0]
                    str_data = str_data + "- {}.\n".format(descr)
                if not results:
                    dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία των καναλιών...")
                else:
                    dispatcher.utter_message(str_data)
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()

        return []

class ActionDbAboutDetails(Action):	
#       Περί διαβατηρίου λεπτομερέστερα
#       Ανάκτηση και εμφάνιση Sort_Description από table "rule" για PS = "Ps0001" και rule.name = 'ABOUT PASSPORT'.
    def name(self):
        return "action_db_about_details"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)
        
        cursor = db.cursor()
        q = "select rule.sort_description from publicservice_rule as ps_rule, rule where ps_rule.identifier_ps = '{}' and ps_rule.identifier_ru = rule.identifier and rule.name = 'ABOUT PASSPORT'".format(IDENTIFIER_PS_PASSPORT)
             
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                descr = row[0]
                dispatcher.utter_message(format(descr))
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()

        return []

class ActionInfo(Action):	
#       Εμφάνιση πληροφοριών ανάπτυξης του Chatbot
    def name(self):
        return "action_info"

    def run(self, dispatcher, tracker, domain):
           
        str_data = "- Το παρόν chatbot 🌏 έχει δημιουργηθεί στο πλαίσιο της Διπλωματικής Εργασίας με θέμα 'Ανάπτυξη ChatBot πληροφόρησης από το δημόσιο τομέα σχετικά με τα ταξίδια στο εξωτερικό' της μεταπτυχιακής φοιτήτριας Ευσεβίας Μπάρτζα. \n"
  
        str_data = str_data + "Το TravelDocBot αποτελεί επέκταση του PassBot, που έχει δημιουργηθεί από τον μεταπτυχιακού φοιτητή του ΕΑΠ Αντωνιάδη Παντελή, στο πλαίσιο της διπλωματικής του εργασίας, κατά το ακαδημαϊκό έτος 2019-2020. \n"
  
        str_data = str_data + "- Η ανάπτυξη του έχει πραγματοποιηθεί με το open source framework 'Rasa'.\n"
        str_data = str_data + "- Η σχετική πληροφορία είναι καταχωρημένη σύμφωνα με το ευρωπαϊκό μοντέλο CPSV-AP με την χρήση της βάσης γνώσης TypeDB, από την οποία πραγματοποιείται on-line ανάκτηση για κάθε ανταπόκριση του ChatBot.\n"
        dispatcher.utter_message(str_data)
        
        str_data = "Καλύπτει την παρακάτω πληροφόρηση σχετικά με το διαβατήριο:\n"
        str_data = str_data + "- Τι είναι διαβατήριο.\n"
        str_data = str_data + "- Προϋποθέσεις έκδοσης διαβατηρίου (συνοπτικά/αναλυτικά).\n"
        str_data = str_data + "- Περιπτώσεις έκδοσης διαβατηρίου.\n"
        str_data = str_data + "- Kόστος έκδοσης διαβατηρίου.\n"
        str_data = str_data + "- Διαδικασία έκδοσης.\n"
        str_data = str_data + "- Δικαιολογητικά που απαιτούνται (λίστα).\n"
        str_data = str_data + "- Εξατομικευμένη πληροφόρηση δικαιολογητικών - Κόστους - Εξόδου διαβατηρίου.\n"
        str_data = str_data + "- Τόπος υποβοβολής των δικαιολογητικών.\n"
        str_data = str_data + "- Εύρεση γραφείου διαβατηρίων περιοχής.\n"
        str_data = str_data + "- Εύρεση γραφείων που λειτουργούν Κυριακή.\n"
        str_data = str_data + "- Διάρκεια ισχύος των διαβατηρίων.\n"
        str_data = str_data + "- Επείγουσα έκδοση διαβατηρίου.\n"      
        str_data = str_data + "- Απώλεια/κλοπή διαβατηρίου.\n"      
        str_data = str_data + "- Στοιχεία που περιλαμβάνει το διαβατήριο.\n"
        str_data = str_data + "- Ακύρωση / Αφαίρεση διαβατηρίου.\n"        
        str_data = str_data + "- Νομοθετικό πλαίσιο.\n"   
        dispatcher.utter_message(str_data)
        
        str_data = "Αποστέλλει και με email, τις σημαντικές πληροφορίες :\n"
        str_data = str_data + "- Εξατομικευμένα δικαιολογητικά - Κόστος - Έξοδος διαβατηρίου.\n"
        str_data = str_data + "- Διαδικασία έκδοσης.\n"
        str_data = str_data + "- Προυποθέσεις έκδοσης.\n"
        str_data = str_data + "- Γραφείο διαβατηρίων περιοχής χρήστη.\n"
        str_data = str_data + "- Ανοικτά Γραφεία Διαβατηρίων την Κυριακή.\n"                
        dispatcher.utter_message(str_data)
        

        str_data = "Καλύπτει την παρακάτω πληροφόρηση σχετικά με την βίζα:\n"
        str_data = str_data + "- Τι είναι βίζα.\n"
        str_data = str_data + "- Για ποιες χώρες απαιτείται βίζα.\n"
        str_data = str_data + "- Διαδικασία έκδοσης.\n"
        str_data = str_data + "- Φορείς έκδοσης.\n"    
        str_data = str_data + "- Δικαιολογητικά που απαιτούνται.\n"
        str_data = str_data + "- Προϋποθέσεις έκδοσης βίζα.\n"
        str_data = str_data + "- Διάρκεια βίζα.\n"
        str_data = str_data + "- Kόστος έκδοσης βίζα.\n"
        dispatcher.utter_message(str_data)

        str_data = "Καλύπτει την παρακάτω πληροφόρηση σχετικά με την Ευρωπαϊκή Κάρτα Ασφάλισης Ασθενείας:\n"
        str_data = str_data + "- Τι είναι Ε.Κ.Α.Α.\n"
        str_data = str_data + "- Σε ποιες χώρες ισχύει.\n"
        str_data = str_data + "- Διαδικασία έκδοσης.\n"
        str_data = str_data + "- Φορείς έκδοσης.\n"    
        str_data = str_data + "- Δικαιολογητικά που απαιτούνται.\n"
        str_data = str_data + "- Προϋποθέσεις έκδοσης Ε.Κ.Α.Α.\n"
        str_data = str_data + "- Διάρκεια Ε.Κ.Α.Α.\n"
        dispatcher.utter_message(str_data)

        str_data = "Επιπλέον καλύπτει :\n"
        str_data = str_data + "- Small talk.\n"
        str_data = str_data + "- Χαιρετισμούς.\n"
        str_data = str_data + "- Ευχαριστίες.\n"
        str_data = str_data + "- Χειρισμό 'out of scope' ερωτήσεων.\n"        
        str_data = str_data + "- Feedback. \nΔίνεται κατά την αποχώρηση του χρήστη, εφόσον υπάρχει χαιρετισμός (πχ αντίο) ή μετά από ευχαριστίες του."
        dispatcher.utter_message(str_data)

        str_data = "Από οποιοδήποτε σημείο του διαλόγου γράφοντας 'Επιλογές' εμφανίζονται με buttons προτεινόμενες επιλογές πληροφόρησης."
        dispatcher.utter_message(str_data)
        
        db = mysql.connector.connect(**config)        
        cursor = db.cursor()

        # Ανάκτηση θετικών εντυπώσεων για το chatbot από talbe "feedback"
        q = "select count(*) from feedback where vote_useful = 'affirm'"
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            i = 0
            for row in results:
                i+=1
                if i==1:
                   useful_affirm = row[0]
            if not results:
                useful_affirm = 0
#                dispatcher.utter_message("Τέλος, δεν βρέθηκαν στοιχεία 'affirm' feedback...")
        except:
            useful_affirm = 0
#            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία 'affirm' feedback...")
        
        # Ανάκτηση αρνητικών εντυπώσεων για το chatbot από talbe "feedback"
        q = "select count(*) from feedback where vote_useful = 'deny'"
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            i = 0
            for row in results:
                i+=1
                if i==1:
                   useful_deny = row[0]
            if not results:
                useful_deny = 0
#                dispatcher.utter_message("Τέλος, δεν βρέθηκαν στοιχεία 'deny' feedback...")
        except:
            useful_deny = 0
#            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία 'deny' feedback...")                               
        
        useful_affirm_per = 0
        useful_deny_per = 0
        if useful_affirm > 0:
            useful_affirm_per = (useful_affirm / (useful_affirm + useful_deny)) * 100
        if useful_deny > 0:
            useful_deny_per = (useful_deny / (useful_affirm + useful_deny)) * 100
        response = ('Τέλος, από την έως τώρα χρήση του Chatbot καταγράφηκαν {} ({:2.1f}%) θετικές εντυπώσεις και {} ({:2.1f}%) αρνητικές.'.format(useful_affirm, useful_affirm_per, useful_deny, useful_deny_per))
        dispatcher.utter_message(response)                           
            
        db.close()        

        return[]

class ActionDbDurationOfPassport(Action):	
#       Διάρκεια ισχύος του διαβατηρίου
#       Ανάκτηση και εμφάνιση Sort_Description από table "rule" για PS = "Ps0001" και rule.name = 'DURATION OF PASSPORT'.
    def name(self):
        return "action_db_duration_of_passport"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)    
        
        cursor = db.cursor()
        q = "select rule.sort_description from publicservice_rule as ps_rule, rule where ps_rule.identifier_ps = '{}' and ps_rule.identifier_ru = rule.identifier and rule.name = 'DURATION OF PASSPORT'".format(IDENTIFIER_PS_PASSPORT)

        response = """Η διαρκεια ισχύος των διαβατηρίων είναι η εξής : """
        dispatcher.utter_message(response)
        
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                descr = row[0]
                dispatcher.utter_message(format(descr))
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")                
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()
        
        return []

class ActionDbEmergencyPassportIssuance(Action):	
#       Επείγουσα έκδοση διαβατηρίου
#       Ανάκτηση και εμφάνιση Sort_Description από table "rule" για PS = "Ps0001" και rule.name = 'EMERGENCY PASSPORT ISSUANCE'.
    def name(self):
        return "action_db_emergency_passport_issuance"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)        
        
        cursor = db.cursor()
        q = "select rule.sort_description from publicservice_rule as ps_rule, rule where ps_rule.identifier_ps = '{}' and ps_rule.identifier_ru = rule.identifier and rule.name = 'EMERGENCY PASSPORT ISSUANCE'".format(IDENTIFIER_PS_PASSPORT)

        response = """Επείγουσα έκδοση διαβατηρίου ; """
        dispatcher.utter_message(response)
        
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                descr = row[0]
                dispatcher.utter_message(format(descr))
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")                
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()
        
        return [] 

class ActionDbLossTheftOofPpassport(Action):	
#       Απώλεια/κλοπή διαβατηρίου
#       Ανάκτηση και εμφάνιση Sort_Description από table "rule" για PS = "Ps0001" και rule.name = 'LOSS-THEFT OF PASSPORT'.
    def name(self):
        return "action_db_loss_theft_of_passport"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)            
        
        cursor = db.cursor()
        q = "select rule.sort_description from publicservice_rule as ps_rule, rule where ps_rule.identifier_ps = '{}' and ps_rule.identifier_ru = rule.identifier and rule.name = 'LOSS-THEFT OF PASSPORT'".format(IDENTIFIER_PS_PASSPORT)
       
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                descr = row[0]
                dispatcher.utter_message(format(descr))
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()
        
        return []   

class ActionDbPassportContent(Action):	
#       Στοιχεία που περιλαμβάνει το διαβατήριο
#       Ανάκτηση και εμφάνιση Sort_Description από table "rule" για PS = "Ps0001" και rule.name = 'PASSPORT CONTENT'.
    def name(self):
        return "action_db_passport_content"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)        
        
        cursor = db.cursor()
        q = "select rule.sort_description from publicservice_rule as ps_rule, rule where ps_rule.identifier_ps = '{}' and ps_rule.identifier_ru = rule.identifier and rule.name = 'PASSPORT CONTENT'".format(IDENTIFIER_PS_PASSPORT)
       
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                descr = row[0]
                dispatcher.utter_message(format(descr))
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()
        
        return []

class ActionDbCancellationOfPassport(Action):	
#       Ακύρωση/Αφαίρεση διαβατηρίου
#       Ανάκτηση και εμφάνιση Sort_Description από table "rule" για PS = "Ps0001" και rule.name = 'CANCELLATION OF PASSPORT'.
    def name(self):
        return "action_db_cancellation_of_passport"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)            

        cursor = db.cursor()
        q = "select rule.sort_description from publicservice_rule as ps_rule, rule where ps_rule.identifier_ps = '{}' and ps_rule.identifier_ru = rule.identifier and rule.name = 'CANCELLATION OF PASSPORT'".format(IDENTIFIER_PS_PASSPORT)
       
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                descr = row[0]
                dispatcher.utter_message(format(descr))
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()
        
        return []

class ActionDbactionDbLegalResource(Action):	
#       Νομοθετικό πλαίσιο
#       Ανάκτηση και εμφάνιση lr.name, lrst.Description από table "Legalresource" για PS = "Ps0001".
    def name(self):
        return "action_db_legal_resource"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)        

        cursor = db.cursor()
        q = "select lr.name, lrst.description from legalresource as lr, publicservice_legalresource as ps_lr, cvlrstatus as lrst where ps_lr.identifier_ps = '{}' and ps_lr.identifier_lr = lr.identifier and lr.status = lrst.code".format(IDENTIFIER_PS_PASSPORT)

        response = """Το νομοθετικό πλαίσιο σχετικά με την έκδοση διαβατηρίων από την Ελληνική Αστυνομία, την ίδρυση της Διεύθυνσης Διαβατηρίων, τις προϋποθέσεις χορήγησης διαβατηρίων, χρονική ισχύς, δικαιολογητικά, διαδικασίες έκδοσης κ.α. είναι το εξής:"""
        dispatcher.utter_message(response)        
       
        try:
            cursor.execute(q)
            results = cursor.fetchall()
            for row in results:
                descr = row[0]
                status = row[1]
                str_data = "- {} / Status: {}".format(descr,status)
                dispatcher.utter_message(str_data)                
            if not results:
                dispatcher.utter_message("Λυπάμαι... Δεν βρέθηκαν τα στοιχεία...")
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ανακτήσω στοιχεία...")
            
        db.close()
        
        return []

class ActionfeedBack(Action):	
#       Εγγραφή feedback από τον χρήστη
    def name(self):
        return "action_db_feedback"

    def run(self, dispatcher, tracker, domain):
        db = mysql.connector.connect(**config)
              
        last_message = tracker.latest_message['intent'].get('name')
        
        cursor = db.cursor()
        q = "insert into feedback (vote_useful) values ('%s')" % (last_message.replace('/', ''))
  
        try:
            cursor.execute(q)
            db.commit()
        except:
            dispatcher.utter_message("Ούπς... ⚙ Δεν μπόρεσα να ενημερώσω την DataBase...")
            
        db.close()
                
        return []      

class ActionDefaultAskAffirmation(Action):
#       Ερώτηση επιβεβαίωσης για πρόθεση χρήστη εφόσον το confidence rate είναι κάτω από το δηλωμένο κατώφλι
    """Asks for an affirmation of the intent if NLU threshold is not met."""

    def name(self) -> Text:
        return "action_default_ask_affirmation"

    def __init__(self) -> None:
        import pandas as pd

        self.intent_mappings = pd.read_csv(INTENT_DESCRIPTION_MAPPING_PATH,encoding ='utf-8')
        self.intent_mappings.fillna("", inplace=True)
        self.intent_mappings.entities = self.intent_mappings.entities.map(
            lambda entities: {e.strip() for e in entities.split(",")}
        )

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        
        # Λήψη της λίστας των ταξινομημένων intents
        intent_ranking = tracker.latest_message.get("intent_ranking", [])
                      
        first_intent_names=[]
        i=0        
        # Εξαγωγή των 2 πρώτων intents, εκτός αυτών που δεν πρέπει να προταθούν
        for row in intent_ranking:
            if row.get("name", "") not in ["q1","q2","q3","q4","q5","q6","q7","q8","q9","q10","q11","q12","enter_email","out_of_scope"]:
               first_intent_names.append(row.get("name", ""))
               i+=1
               if i >= 2:
                  break
                
        message_title = (
            "Δυστυχώς δεν είμαι σίγουρος ότι κατάλαβα σωστά 🤔 Εννοείς..."
        )

        entities = tracker.latest_message.get("entities", [])
        entities = {e["entity"]: e["value"] for e in entities}

        entities_json = json.dumps(entities)

        buttons = []
        for intent in first_intent_names:
            button_title = self.get_button_title(intent, entities)
            if "/" in intent:
                # here we use the button title as the payload as well, because you
                # can't force a response selector sub intent, so we need NLU to parse
                # that correctly
                buttons.append({"title": button_title, "payload": button_title})
            else:
                buttons.append(
                    {"title": button_title, "payload": f"/{intent}{entities_json}"}
                )

        buttons.append({"title": "Κάτι άλλο", "payload": "/trigger_rephrase"})

        dispatcher.utter_message(text=message_title, buttons=buttons)

        return []    

    def get_button_title(self, intent: Text, entities: Dict[Text, Text]) -> Text:
        default_utterance_query = self.intent_mappings.intent == intent
        utterance_query = (self.intent_mappings.entities == entities.keys()) & (
            default_utterance_query
        )

        utterances = self.intent_mappings[utterance_query].button.tolist()

        if len(utterances) > 0:
            button_title = utterances[0]
        else:
            utterances = self.intent_mappings[default_utterance_query].button.tolist()
            button_title = utterances[0] if len(utterances) > 0 else intent

        return button_title.format(**entities)

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        # Fallback caused by TwoStageFallbackPolicy
        if (
            len(tracker.events) >= 4
            and tracker.events[-4].get("name") == "action_default_ask_affirmation"
        ):

            dispatcher.utter_message(template="utter_restart_with_button")

            return []
            
        # Fallback caused by Core
        else:
            dispatcher.utter_message(template="utter_default")
            return [UserUtteranceReverted()] 
            