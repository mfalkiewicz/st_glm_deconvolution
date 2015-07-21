class stdec(object):
    def __init__(self,nick,filename,cond_cols,conditions,cond_pattern):
        import numpy as np
        import pandas as pd
        import os
        import math
        import random
        self.filename=filename # Presentation logfile
        self.nick = nick # subject nickname
        self.cond_cols = cond_cols # logfile columns neccessary for trial classification
        self.conditions = conditions # array of conditions
        self.cond_pattern = np.array(cond_pattern) # dict of regular expressions for condition classification

    def read_logfile(self):
        import pandas as pd
        self.data = pd.read_table(self.filename,sep = "\t",skiprows=[1])

    def getconds(self):
        import pandas as pd
        import numpy as np
        import re
        self.f_conds = np.array(self.data.Code)
        self.f_onsets = np.array(self.data.Time)
        self.stime = self.f_onsets[self.f_conds == 'start']
        self.f_onsets = self.f_onsets - self.stime
        self.f_onsets = self.f_onsets/10000.
        self.f_durations = np.array(self.data.Duration)
        self.f_durations = self.f_durations/10000.
        self.f_responses = np.array(self.data.Type)
        self.labels = []
        self.onsets = []
        self.durations = []
        self.evcount = []

        # Loop over conditions
        for i, c in enumerate(self.cond_pattern):
            self.idx = {} # Store match indexes

            for k, v in enumerate(self.cond_cols):
                self.idx[v] = [] # Make empty dictionary for indexes
                # Compile the pattern
                self.p = re.compile(c[k][0])

                # Loop over all values in the column
                for w, l in enumerate(self.data[self.cond_cols[k]]):
                    m = self.p.match(l)
                    if m:
                        self.idx[v].append(w)

            # Get common indexes for all idx dict entries
            self.cidx = self.idx[self.cond_cols[0]]
            for j, v in enumerate(self.cond_cols):
                self.cidx = np.intersect1d(self.cidx,self.idx[v])
            if len(self.cidx > 0):
                self.e_onsets = self.f_onsets[self.cidx].tolist()
                self.e_durations = self.f_durations[self.cidx].tolist()
                self.e_labels = np.repeat(self.conditions[i],len(self.e_onsets))
                self.labels.append(self.e_labels)
                self.onsets.append(self.e_onsets)
                self.durations.append(self.e_durations)
                # Also add count of events for each condition
                self.evcount.append(len(self.e_onsets))

    def collapse_dm(self):
        import numpy as np

        self.all_labels = np.concatenate(self.labels)
        self.all_onsets = np.concatenate(self.onsets)
        self.all_durations = np.concatenate(self.durations)

    def extract_events(self):
        import numpy as np

        self.single_events = {}
        for i, v in enumerate(self.all_onsets):
            slabel = self.all_labels[i]
            sonset = self.all_onsets[i]
            sdur = self.all_durations[i]
            clabels = np.delete(self.all_labels,i)
            consets = np.delete(self.all_onsets,i)
            cdurs = np.delete(self.all_durations,i)
            self.single_events[i] = [[clabels,[slabel]],[consets,[sonset]],[cdurs,[sdur]]]
