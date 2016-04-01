from client.protocols.common import models
from client.utils import auth
from client.utils import assess_id_util
import json
import logging
import os
import sys
from urllib.request import urlopen

log = logging.getLogger(__name__)

"""
This utility is called by unlock.py. This guidance utility changes the message that students see
after they input in wrong answers. If a student guesses a certain amount of wrong answers
that shows a certain type of confusion about the problem, this utility will instead of showing
the default "Not Quite Try Again" message will show some kind of message that will target
that type of misunderstanding.

This utility object requires internet access to determine what treatment group they are assigned
to. The different treatment groups will have varying threshold level of answers as well as different
messages and other differences. It will contact the server defined below in the variable TGSERVER with
the user's email and lab assignment to get the treatment group number.

Commonly used acronyms:
TG = treatment group number
KI = Type of targeted understanding
misU = Type of misunderstanding the student is showing
wa

The LOCAL_TG_FILE will hold what treatment group number the student is part of.
The OK_GUIDANCE_FILE will facilitate the generation of guided messages. It will hold the necessary info
to know what type of misunderstanding an answer has as well as what guidance message to show.
"""

TGSERVER = "https://tg-server.app.cs61a.org/"
TG_SERVER_ENDING = "/unlock_tg"

LOCAL_TG_FILE = "tests/tg.ok_tg"
OK_GUIDANCE_FILE = "tests/.ok_guidance"
GUIDANCE_DEFAULT_MSG = "-- Not quite. Try again! --"
EMPTY_MISUCOUNT_TGID_PRNTEDMSG = ({}, -1, "")
COUNT_FILE_PATH = "tests/misUcount.json"
TG_CONTROL = 0
# If student forces guidance messages to show, we will assign treatment group number below
GUIDANCE_FLAG_TG_NUMBER = 1
#If set_tg() fails, we will default to this treatment group number
TG_ERROR_VALUE = -1

#These lambda functions allow us to map from a certain type of misunderstanding to
#the desired targeted guidance message we want to show.
# lambda for control or treatment group where we want nothing to happen
# Knowledge integration treatment group lambda that is answer specific
# lambda for returning an answer + misunderstanding specific message

lambda_string_key_to_func = {
    'none': lambda info, strMisU: None,
    'ki': lambda info, strMisU: info['ki'],
    'misU2Msg': lambda info, strMisU: info['dictMisU2Msg'].get(strMisU)
}

class Guidance:
    def __init__(self, current_working_dir):
        """
        Initializing everything we need to the default values. If we catch
        an error when opening the JSON file, we flagged it as error.
        """
        self.tg_id = -1
        self.misU_count_dict = {} #Maps the type of misunderstanding seen to the number of times seen
        self.current_working_dir = current_working_dir
        try:
            with open(current_working_dir + OK_GUIDANCE_FILE,"r") as f:
                self.guidance_json = json.load(f)
            self.load_error = False
        except IOError as e:
            log.warning("Failed to read .ok_guidance file in guidance.py. IOError")
            self.load_error = True
        except ValueError as e:
            log.warning("Failed to read .ok_guidance file in guidance.py. ValueError")
            self.load_error = True


    def show_guidance_msg(self,unique_id, input_lines,access_token,hash_key,guidance_flag):
        """
        Based on the student's answer (input_lines), we grab each associated
        message if its corresponding misunderstanding's count is above the threshold
        """
        if self.load_error:
            print (GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        shorten_unique_id = assess_id_util.canonicalize(unique_id)
        # Try to get the info dictionary for this question. Maps wrong answer to dictionary
        Wrong_Answer_2_dict_info = self.guidance_json['dictAssessId2WA2DictInfo'].get(shorten_unique_id)

        if not Wrong_Answer_2_dict_info: # get returns None if Wrong_Answer_2_dict_info doesn't have shorten_unique_id in dictionary
            print (GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        dict_info = Wrong_Answer_2_dict_info.get(repr(input_lines))

        # If this wrong answer is not in the JSON file, display default message
        if not dict_info:
            print (GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        self.set_tg(access_token,guidance_flag)
        if self.tg_id == TG_ERROR_VALUE:
            # If self.tg_id == -1, some errors happen when trying to access server
            print (GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        lambda_string_key = self.guidance_json['dictTg2Func'].get(str(self.tg_id))

        if not lambda_string_key:
            print (GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        lambda_info_misu = lambda_string_key_to_func.get(lambda_string_key)
        if not lambda_info_misu:
            print (GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        lst_mis_u = dict_info.get('lstMisU')

        # No list of misunderstandings for this wrong answer, default message
        if not lst_mis_u:
            print (GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        self.misU_count_dict = self.update_misUcounts(hash_key, lst_mis_u, repr(input_lines),shorten_unique_id)

        Wrong_Answer_threshold = self.guidance_json['wrongAnsThresh']

        msg_id_set = set()

        # If the count is higher than the threshold, we need to display the message
        for mis_u in self.misU_count_dict:
            if self.misU_count_dict[mis_u] >= Wrong_Answer_threshold:
                # Add each associated misunderstanding ID to the set
                msg_id = lambda_info_misu(dict_info, mis_u)

                if msg_id:
                    msg_id_set.add(msg_id)

        if len(msg_id_set) == 0 or self.tg_id == TG_CONTROL:
            # if student is in control group, just print the default message
            print (GUIDANCE_DEFAULT_MSG)
            return (self.misU_count_dict, self.tg_id,"")

        print ("-- Helpful Hint --\n")

        printed_out_msgs = ""
        for message_id in msg_id_set:
            msg = self.guidance_json['dictId2Msg'][str(message_id)]
            printed_out_msgs = printed_out_msgs + msg
            print (msg)
        print(GUIDANCE_DEFAULT_MSG)
        print ()

        return (self.misU_count_dict, self.tg_id,printed_out_msgs)

    def update_misUcounts(self, hashkey, lst_misU, wrongAnswer, shorten_unique_id):
        """
        Looks at the locally saved file for number of misU and returns the current count
        for each misunderstanding. Also updates the count with the most recent user input
        """

        #Creates a new folder inside tests that stores the number of misU per assignment
        if os.path.isfile(self.current_working_dir + COUNT_FILE_PATH):
            with open(self.current_working_dir + COUNT_FILE_PATH,'r') as f:
                jsonDic = json.load(f)
                answerDict = jsonDic["answerDict"]
                countData = jsonDic["countData"]
        else:
            countData = {}
            answerDict = {}

        # Checks to see if the question is already stored and whether the student's answer is there
        # It does not update misU count if same answer was seen before
        if shorten_unique_id in answerDict and wrongAnswer in answerDict[shorten_unique_id]:
            return countData
        if not shorten_unique_id in answerDict:
            answerDict[shorten_unique_id] = []

        # Updates misU count
        for answer_MisU in lst_misU:
            if answer_MisU in countData:
                countData[answer_MisU] += 1
            else:
                countData[answer_MisU] = 1

        # Stores the updated count back into the same file and overrides it
        newjsonDic = {}
        answerDict[shorten_unique_id].append(wrongAnswer)
        newjsonDic["countData"] = countData
        newjsonDic["answerDict"] = answerDict
        with open(self.current_working_dir + COUNT_FILE_PATH,"w") as f:
            json.dump(newjsonDic,f)
        # Returns a dictionary containing how many times each misU has been seen.
        return countData

    def set_tg(self,access_token,guidance_flag):
        """
        Try to grab the treatment group number for the student. If there is no treatment
        group number available, we request it from the server.
        """
        if guidance_flag:
            with open(self.current_working_dir + LOCAL_TG_FILE,"w") as f:
                f.write(str(GUIDANCE_FLAG_TG_NUMBER))
            self.tg_id = GUIDANCE_FLAG_TG_NUMBER
            return

        # Checks to see the student currently has a treatment group number. If not, calls helper function in auth.py
        if not os.path.isfile(self.current_working_dir + LOCAL_TG_FILE):
            cur_email = auth.get_student_email(access_token)
            if not cur_email:
                self.tg_id = -1
                return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

            try:
                data = json.loads(urlopen(TGSERVER + cur_email + TG_SERVER_ENDING,timeout =1).read().decode("utf-8"))
            except IOError as e:
                data = {"tg":-1}

            with open(self.current_working_dir + LOCAL_TG_FILE,"w") as fd:
                fd.write(str(data["tg"]))
        tg_file = open(self.current_working_dir + LOCAL_TG_FILE, 'r')
        self.tg_id = int(tg_file.read())
