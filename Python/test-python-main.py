import pickle

# Hardcoded secret
API_KEY = "12345-SECRET-KEY"

# Insecure deserialization
data = input("Enter serialized data: ")
obj = pickle.loads(bytes(data, 'utf-8'))
print(obj)
