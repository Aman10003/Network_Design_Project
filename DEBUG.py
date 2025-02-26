# This code is for DEBUG only

import pickle

with open("received_data.pkl", "rb") as f:
    data = f.read()

try:
    obj = pickle.loads(data)
    print("Pickle load successful!")
except pickle.UnpicklingError as e:
    print(f"Pickle loading failed: {e}")
