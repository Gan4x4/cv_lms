import numpy as np


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
    # Convert to a plain numpy array before locating non-empty rows.
    # Older pandas/numpy combinations can mis-handle np.argwhere on Series.
    idx = np.flatnonzero(~topics.isnull().to_numpy())
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
