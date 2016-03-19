from client.protocols.common import models
from client.utils import auth
from urllib.request import urlopen
import json
import os
import sys

TGSERVER = "http://tg-server.app.cs61a.org/"
LOCAL_TG = "tests/tg.ok_tg"
OK_GUIDANCE = "tests/.ok_guidance"

lambda_string_key_to_func = {
    'none': lambda info, strMisU: None, 
    'ki': lambda info, strMisU: info['ki'],
    'reteach': lambda info, strMisU: info['dictMisU2ReteachMsg'].get(strMisU)
}
  
# If student forces guidance messages to show, we will assign treatment group number below
guidance_flag_dict = [1]

class GuidanceProtocol(models.Protocol):
    def __init__(self,working_dir,debug = -1):
        self.tg_id = -1
        self.msg_id = -1
        self.misU_count = {}
        self.working_dir = working_dir
        self.debug = debug
        try:
            with open(working_dir + OK_GUIDANCE,"r") as f:
                self.guidance_json = json.load(f)
            self.error = False
        except:
            self.error = True

    def guidance_msg(self,unique_id, input_lines,access_token,hash_key,guidance_flag):
        if self.error:
            print ("-- Not quite. Try again! --")
            return ({}, -1,"")

        shorten_unique_id = unique_id[unique_id.index('\n')+1:]
        # Try to get th info dictionary for this question
        wa_2_dict_info = self.guidance_json['dictAssessId2WA2DictInfo'].get(shorten_unique_id)

        if not wa_2_dict_info: # get returns None if wa_2_dict_info doesn't have shorten_unique_id in dictionary
            print ("-- Not quite. Try again! --")
            return ({}, -1,"")

        dict_info = wa_2_dict_info.get(repr(input_lines))

        # If this wrong answer is not in the JSON file, display default message
        if not dict_info:            
            print ("-- Not quite. Try again! --")
            return ({}, -1,"")
        if(self.debug != -1):
            self.tg_id = self.debug
        else:
            self.get_tg(access_token,guidance_flag)

        if self.tg_id == -1: 
            # If self.tg_id == -1, some errors happen when trying to access server
            print ("-- Not quite. Try again! --")
            return ({}, -1,"")

        lambda_string_key = self.guidance_json['dictTg2Func'].get(str(self.tg_id))

        if not lambda_string_key:
            print ("-- Not quite. Try again! --")
            return ({}, -1,"")

        lambda_info_misu = lambda_string_key_to_func.get(lambda_string_key)

        lst_mis_u = dict_info.get('lstMisU')

        # No list of misunderstandings for this wrong answer, default message
        if not lst_mis_u:
            print ("-- Not quite. Try again! --")
            return ({}, -1,"")

        self.misU_count = self.update_misUcounts(hash_key, lst_mis_u, repr(input_lines),shorten_unique_id)

        thresold = self.guidance_json['wrongAnsThresh']

        """
        Update count file using the helper. Each misunderstanding igets one count.

        Get the updated acculamted counts as a dictionary: key: mis_u, value: counts.
        
        Called that dictionary self.misU_count
        """

        self.msg_id_set = set()

        # If the count is higher than the thresold, we need to display the message
        for mis_u in self.misU_count:
            if self.misU_count[mis_u] >= thresold:
                # Print each associated unique message for each miunderstanding
                self.msg_id = lambda_info_misu(dict_info, mis_u)

                if self.msg_id:
                    self.msg_id_set.add(self.msg_id)

        if len(self.msg_id_set) == 0 or None in self.msg_id_set:
            # if student is in control group, just print the default message
            print ("-- Not quite. Try again! --")
            return (self.misU_count, self.tg_id,"")

        print("-- Helpful Hint --\n")

        printed_out_msgs = ""
        for mid in self.msg_id_set:
            msg = self.guidance_json['dictId2Msg'][str(mid)]
            printed_out_msgs = printed_out_msgs + msg
            print(msg)

        print("\n-- Helpful Hint --")

        return (self.misU_count, self.tg_id,printed_out_msgs)

    # Looks at the locally saved file for number of misU and returns the current count
    def update_misUcounts(self, hashkey, misU, wrongAnswer, shorten_unique_id):
        #Creates a new folder inside tests that stores the number of misU per assignment
        count_file_path = "tests/misUcount.json"
        if os.path.isfile(self.working_dir + count_file_path):
            with open(self.working_dir + count_file_path,'r') as f:
                jsonDic = json.load(f)
                answerDict = jsonDic["answerDict"]
                countData = jsonDic["countData"] 
        else:
            countData = {}
            answerDict = {}
        newjsonDic = {}

        # Checks to see if the question is already stored and whether the student's answer is there
        # It does not update misU count if same answer was seen before
        if shorten_unique_id in answerDict and wrongAnswer in answerDict[shorten_unique_id]:
            return countData
        if not shorten_unique_id in answerDict:
            answerDict[shorten_unique_id] = []

        # Updates misU count
        for x in misU: 
            if x in countData:
                countData[x] += 1
            else:
                countData[x] = 1

        # Stores the updated count back into the same file and overrides it
        answerDict[shorten_unique_id].append(wrongAnswer)
        newjsonDic["countData"] = countData
        newjsonDic["answerDict"] = answerDict
        with open(self.working_dir + count_file_path,"w") as f:
            json.dump(newjsonDic,f)
        # Returns a dictionary containing how many times each misU has been seen.
        return countData

    def get_tg(self,access_token,guidance_flag):
        if guidance_flag:
            with open(self.working_dir + LOCAL_TG,"w") as f:
                f.write(str(guidance_flag_dict[0]))
            self.tg_id = guidance_flag_dict[0]
            return
        # Checks to see the student currently has a treatment group number. If not, calls helper function in auth.py
        if not os.path.isfile(self.working_dir + LOCAL_TG):
            cur_email = auth.get_student_email(access_token)
            if not cur_email:
                print ("--Not quite. Try again! --")
                return ({}, -1)
            try:
                data = json.loads(urlopen(TGSERVER + cur_email + "/unlock_tg",timeout =1).read().decode("utf-8"))
            except IOError as e:
                data = {"tg":-1}
            fd = open(self.working_dir + LOCAL_TG,"w")
            fd.write(str(data["tg"]))
            fd.close()

        tg_file = open(self.working_dir + LOCAL_TG, 'r')
        self.tg_id = int(tg_file.read())
protocol = GuidanceProtocol