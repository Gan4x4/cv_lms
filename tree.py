import csv
import numpy as np


def read_csv(filename):
    data = []
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            data.append(row)
    return data


def pairwise(t):
    it = iter(t)
    return zip(it, it)


def is_empty(df):
    bool_mask = ~df.isnull()
    int_mask = bool_mask.to_numpy() * 1
    if int_mask.sum() == 0:
        return True
    if not (len(df)) or not (len(df.iloc[0])):
        return True
    return False


def tree(data):
    # leaf
    if is_empty(data):
        return {}
    childs = {}
    topics = data.iloc[:, 0]
    idx = np.argwhere(~topics.isnull()).flatten()
    if len(idx) == 0:  # first column are empty, so skip it
        crop = data.iloc[:, 1:]
        childs = tree(crop)
    else:
        for i in range(len(idx)):
            f = idx[i]
            if i < len(idx) - 1:
                t = idx[i + 1]
            else:
                t = len(data)
            crop = data.iloc[f:t, 1:]
            v = topics.iloc[f]
            childs[v] = tree(crop)

    return childs


#def download_topics(filename="questions.csv"):
#    if os.path.exists(filename):
#        os.remove(filename)  # if
#    url = 'https://docs.google.com/spreadsheets/d/1TfAWZkN1dA-ftaSONKegxrnF12kO35ZwClaBhIkGszY/export?gid=1315115932&format=csv'
#    wget.download(url, out=filename)

# download_topics()

# data = read_csv("questions.csv")
# data = pd.read_csv("questions.csv")
# print(tree("tmp",data.iloc[:,1:5]))
