from stdec import stdec

nick = "testsub"
conditions = ["PT","WT","PL","WL","AT","PTerr","WTerr","PLerr","WLerr","ATerr","miss"]
cond_cols = ["Code","Type"]
cond_pattern = [ [['zucz*'],['hit']],[['zsw*'],['hit']],
    [['nucz*'],['incorrect']],[['nsw*'],['incorrect']],
    [['zaut*'],['hit']], [['zucz*'],['incorrect']],
    [['zsw*'],['incorrect']],[['nucz*'],['hit']],
    [['nsw*'],['hit']],[['zaut*'],['incorrect']], [['.*'],['miss']]]


test = stdec(nick,"test.log",cond_cols,conditions,cond_pattern)
test.read_logfile()
test.getconds()
test.collapse_dm()
test.extract_events()
