#!/usr/bin/env python3

# Copyright 2020 University of Stuttgart (Pavel Denisov)
#  Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)

import pandas as pd
import os
import sys
import subprocess
import re

if len(sys.argv) != 2:
    print("Usage: python data_prep.py [root]")
    sys.exit(1)
root = sys.argv[1]

dir_dict = {
    "train": "slue-voxpopuli_fine-tune.tsv",
    "devel": "slue-voxpopuli_dev.tsv",
    "test": "slue-voxpopuli_test_blind.tsv",
}

ontonotes_to_combined_label = {
    "GPE": "PLACE",
    "LOC": "PLACE",
    "CARDINAL": "QUANT",
    "MONEY": "QUANT",
    "ORDINAL": "QUANT",
    "PERCENT": "QUANT",
    "QUANTITY": "QUANT",
    "ORG": "ORG",
    "DATE": "WHEN",
    "TIME": "WHEN",
    "NORP": "NORP",
    "PERSON": "PERSON",
    "LAW": "LAW"
}


missing_count = 0
missing_ent = set()

for x in dir_dict:
    with open(os.path.join("data", x, "text"), "w") as text_f, open(
        os.path.join("data", x, "wav.scp"), "w"
    ) as wav_scp_f, open(
        os.path.join("data", x, "utt2spk"), "w"
    ) as utt2spk_f:

        text_f.truncate()
        wav_scp_f.truncate()
        utt2spk_f.truncate()
        transcript_df = pd.read_csv(os.path.join(root, dir_dict[x]), sep='\t')
        # lines = sorted(transcript_df.values, key=lambda s: s[0])
        for row in transcript_df.values:
            uttid=row[3]+"_"+row[0]
            speaker=row[3]
            if x=="train":
                wav="fine-tune_wav/"+row[0]+".wav"
            elif x=="devel":
                wav="dev_wav/"+row[0]+".wav"
            else:
                wav="test_wav/"+row[0]+".wav"

            transcript=row[2].lower()
            entities = []
            if x!="test":# blind test set
                if str(row[6])!="None":
                    for slot in row[6].split('], '):
                        ent_type = (
                            slot
                            .split(",")[0]
                            .replace("[","")
                            .replace("]","")
                            .replace('"','')
                            .replace("'","")
                        )
                        if ent_type in ontonotes_to_combined_label:
                            ent_type = ontonotes_to_combined_label[ent_type]
                        else:
                            missing_count += 1
                            missing_ent.add(ent_type)
                            continue
                        fill_start = int(
                            slot
                            .split(",")[1]
                            .replace("[","")
                            .replace("]","")
                            .replace('"','')
                            .replace("'","")
                            .replace(" ","")
                        )
                        fill_len = int(
                            slot
                            .split(",")[2]
                            .replace("[","")
                            .replace("]","")
                            .replace('"','')
                            .replace("'","")
                            .replace(" ","")
                        )
                        filler = transcript[fill_start:fill_start+fill_len]
                        entities.append({"type": ent_type, "filler": filler, "filler_start":fill_start, "filler_end": fill_start+fill_len})
            sortednames=sorted(entities, key=lambda x:x["type"].lower())
            new_transcript = transcript[:]
            for entity in entities:
                new_transcript = new_transcript[:entity["filler_start"]] + entity["type"] + " FILL " + entity["filler"].lower() + " SEP " + new_transcript[entity["filler_end"]:]

            if False and x == "devel":
                import pdb; pdb.set_trace()
            predict_sent=""
            for k in sortednames:
                predict_sent+=k["type"]+" fill "+k["filler"].lower()+" SEP "
            predict_sent+= transcript
            words = "{}".format(
                new_transcript
            ).replace("<unk>", "unknown")
    
            text_f.write("{} {}\n".format(uttid, words))
            utt2spk_f.write("{} {}\n".format(uttid, speaker))
            wav_scp_f.write("{} {}\n".format(uttid,os.path.join(root,wav)))

print("Missing Entities", missing_ent)
print("Missing Count", missing_count)
