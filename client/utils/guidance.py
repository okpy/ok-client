from client.utils import auth
from client.utils import assess_id_util

import hashlib
import json
import logging
import os
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
wa = wrong answer

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
# If student forces guidance messages to show, we will assign treatment
# group number below
GUIDANCE_FLAG_TG_NUMBER = 1
# If set_tg() fails, we will default to this treatment group number
TG_ERROR_VALUE = -1

# These lambda functions allow us to map from a certain type of misunderstanding to
# the desired targeted guidance message we want to show.
# lambda for control or treatment group where we want nothing to happen
# Knowledge integration treatment group lambda that is answer specific
# lambda for returning an answer + misunderstanding specific message

lambda_string_key_to_func = {
    'none': lambda info, strMisU: None,
    'ki': lambda info, strMisU: info['ki'],
    'misU2Msg': lambda info, strMisU: info['dictMisU2Msg'].get(strMisU),
    'tag2KIMsg': lambda info, strMisU: info['dictTag2KIMsg'].get(strMisU),
    'tag2ConceptMsg': lambda info, strMisU: info['dictTag2ConceptMsg'].get(strMisU)
}


def hash_dict(contents, expected):
    """ <Fill in hashing function here - order is not constant. > """
    return True


class Guidance:
    def __init__(self, current_working_dir, assignment=None):
        """
        Initializing everything we need to the default values. If we catch
        an error when opening the JSON file, we flagged it as error.
        """
        self.tg_id = -1

        self.assignment = assignment
        if assignment:
            self.assignment_name = assignment.name.replace(" ", "")
        else:
            self.assignment_name = ""

        self.current_working_dir = current_working_dir
        try:
            with open(current_working_dir + OK_GUIDANCE_FILE, "r") as f:
                self.guidance_json = json.load(f)
            self.load_error = False
            if not self.validate_json():
                raise ValueError("JSON did not validate")
            self.guidance_json = self.guidance_json['db']
        except (IOError, ValueError):
            log.warning("Failed to read .ok_guidance file.", exc_info=True)
            self.load_error = True
        log.debug("Guidance loaded with status: %s", not self.load_error)

    def validate_json(self):
        """ Ensure that the checksum matches. """
        if not hasattr(self, 'guidance_json'):
            return False

        checksum = self.guidance_json.get('checksum')
        contents = self.guidance_json.get('db')

        if not checksum:
            log.warning("Checksum on guidance not found. Invalidating file")
            return False

        if not hash_dict(contents, checksum):
            log.warning("Checksum did not match digest")
            return False
        return True

    def show_guidance_msg(self, unique_id, input_lines, access_token, hash_key,
                          guidance_flag=False):
        """
        Based on the student's answer (input_lines), we grab each associated
        message if its corresponding misunderstanding's count is above the threshold
        """
        if self.load_error:
            print(GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        response = repr(input_lines)
        self.set_tg(access_token)
        log.info("Guidance TG is %d", self.tg_id)

        if self.tg_id == TG_ERROR_VALUE:
            # If self.tg_id == -1, there was an error when trying to access the server
            log.warning("Error when trying to access server. TG == -1")
            print(GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        lambda_string_key = self.guidance_json[
            'dictTg2Func'].get(str(self.tg_id))

        if not lambda_string_key:
            log.info("Cannot find the correct lambda in the dictionary.")
            print(GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        lambda_info_misu = lambda_string_key_to_func.get(lambda_string_key)
        if not lambda_info_misu:
            log.info("Cannot find info misU given the lambda string key.")
            print(GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        shorten_unique_id = assess_id_util.canonicalize(unique_id)
        # Try to get the info dictionary for this question. Maps wrong answer
        # to dictionary
        assess_dict_info = self.guidance_json[
            'dictAssessId2Info'].get(shorten_unique_id)
        if not assess_dict_info:
            log.info("shorten_unique_id is not in dictAssessId2Info")
            print(GUIDANCE_DEFAULT_MSG)
            return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

        wa_details = assess_dict_info['dictWA2DictInfo'].get(response)
        if not wa_details:
            log.info("Cannot find the wrong answer in the WA2Dict for this assesment.")
            lst_mis_u = None
        else:
            lst_mis_u = wa_details.get('lstMisU')

        # No list of misunderstandings for this wrong answer, default message
        if not lst_mis_u:
            log.info("Cannot find the list of misunderstandings.")

        wa_count_threshold = self.guidance_json['wrongAnsThresh']
        wa_lst_assess_num = assess_dict_info['dictWA2LstAssessNum_WA']
        msg_id_set = set()

        answerDict, countData = self.get_misUdata()
        prev_responses = answerDict.get(shorten_unique_id, [])

        # Confirm that this WA has not been given before
        seen_before = any(wa in prev_responses for wa in prev_responses)

        answerDict[shorten_unique_id] = prev_responses + [response]
        self.save_misUdata(countData, answerDict)

        if not seen_before:
            # Lookup the list of assessNum and WA related to this wrong answer
            # in the question's dictWA2LstAssessNum_WA
            lst_assess_num = wa_lst_assess_num.get(response)
            if not lst_assess_num:
                log.info("Cannot get the lst of assess nums given this reponse.")
                print(GUIDANCE_DEFAULT_MSG)
                return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

            # Check in answerDict to see if the student has ever given
            # any of these wrong answers (sourced from dictWA2LstAssessNum_WA)
            has_given_resp = any(other_resp in prev_responses for
                                 _, other_resp in lst_assess_num)

            if not has_given_resp:
                log.info("Student has not given a response in dictWA2LstAssessNum_WA.")
                print(GUIDANCE_DEFAULT_MSG)
                return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

            # Check if the current wrong answer is in the question's dictWA2DictInfo
            if not wa_details:
                # Increment countDict by the number of wrong answers seen
                # for each tag assoicated with this wrong answer
                for misu in lst_mis_u:
                    countData[misu] += min(len(prev_responses), 1)
            else:
                # Lookup the lst_mis_u of each wrong answer in the list of wrong
                # answers related to the current wrong answer (lst_assess_num),
                # using dictAssessNum2AssessId
                assess_num_to_aid = self.guidance_json['dictAssessNum2AssessId']

                # misu -> list of wrong answers for that
                related_misu_tags_dict = {}

                for related_num, related_resp in lst_assess_num:
                    related_aid = assess_num_to_aid[related_num]
                    # Get the lst_misu for this asssigmment
                    related_info = self.guidance_json['dictAssessId2Info'].get(related_aid)
                    if not related_info:
                        log.info("Could not find related id: %s in info dict",
                                 related_aid)
                        continue
                    related_wa_info = related_info['dictWA2DictInfo'].get(related_resp)
                    if not related_info:
                        log.info("Could not find response %s in %s info dict",
                                 related_resp, related_aid)
                        continue
                    related_misu_list = related_wa_info['lstMisU']
                    for misu in related_misu_list:
                        existing_resps = related_misu_tags_dict.get(misu, [])
                        # Add dictWA2DictInfo to list of responses for this misunderstanding.
                        related_misu_tags_dict[misu] = existing_resps + [related_wa_info]

                for misu, wa_info in related_misu_tags_dict.values():
                    # Increment countDict for each tag in the set of tags for each related resp
                    countData[misu] += 1

                    # For each mis_u above threshold go through each related wrong answer
                    # Add the msg_id that is given from lambda_info_misu to msg_id_set
                    if countData[misu] > wa_count_threshold:
                        msg_id_set.add(lambda_info_misu(wa_info, misu))

        log.info("Lambda Group: %s", lambda_string_key)

        if len(msg_id_set) == 0:
            log.info("No messages to display. Most likely hasn't hit the wrong answer threshold")
            print(GUIDANCE_DEFAULT_MSG)
            return (countData, self.tg_id, "")

        print("-- Helpful Hint --\n")

        printed_out_msgs = ""
        for message_id in msg_id_set:
            msg = self.guidance_json['dictId2Msg'][str(message_id)]
            printed_out_msgs = printed_out_msgs + msg
            print(msg)
        print()
        print(GUIDANCE_DEFAULT_MSG)

        return (countData, self.tg_id, printed_out_msgs)

    def get_misUdata(self):
        # Creates a new folder inside tests that stores the number of misU per
        # assignment
        if os.path.isfile(self.current_working_dir + COUNT_FILE_PATH):
            with open(self.current_working_dir + COUNT_FILE_PATH, 'r') as f:
                jsonDic = json.load(f)
                answerDict = jsonDic["answerDict"]
                countData = jsonDic["countData"]
        else:
            countData = {}
            answerDict = {}

        return answerDict, countData

    def save_misUdata(self, countData, answerDict):
        data = {
            "countData": countData,
            "answerDict": answerDict
        }
        log.info("Attempting to save response/count dict")
        with open(self.current_working_dir + COUNT_FILE_PATH, "w") as f:
            json.dump(data, f)
        return data

    def set_tg(self, access_token):
        """ Try to grab the treatment group number for the student.
        If there is no treatment group number available, request it
        from the server.
        """
        # Checks to see the student currently has a treatment group number. If
        # not, calls helper function in auth.py
        if not os.path.isfile(self.current_working_dir + LOCAL_TG_FILE):
            cur_email = auth.get_student_email(access_token)
            if not cur_email:
                self.tg_id = -1
                return EMPTY_MISUCOUNT_TGID_PRNTEDMSG

            tg_url = ("{}{}/{}{}"
                      .format(TGSERVER, cur_email, self.assignment_name,
                              TG_SERVER_ENDING))
            try:
                log.info("Accessing treatment server at %s", tg_url)
                data = json.loads((urlopen(tg_url, timeout=1).read()
                                                             .decode("utf-8")))
            except IOError:
                data = {"tg": -1}
                log.error("Failed to communicate to server", exc_info=True)

            if data.get("tg") is None:
                log.error("Server returned back a bad treatment group ID.")
                data = {"tg": -1}

            with open(self.current_working_dir + LOCAL_TG_FILE, "w") as fd:
                fd.write(str(data["tg"]))

        tg_file = open(self.current_working_dir + LOCAL_TG_FILE, 'r')
        self.tg_id = int(tg_file.read())
