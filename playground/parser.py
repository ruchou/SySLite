import pyfsdb
db = pyfsdb.Fsdb("detected_seq.fsdb")
print(db.column_names)
for row in db:
    print(row)