# Python program to read CSV file line by line
# import necessary packages
import csv

# Open file
with open('D:/Polk/epa_vmt_202301.csv') as file_obj:
    # Create reader object by passing the file
    # object to reader method
    reader_obj = csv.reader(file_obj)

    # Iterate over each row in the csv
    # file using reader object
    a = 0
    for row in reader_obj:
        a = a + 1
        # print(row)
        b = row
        print(len(b))
        if a == 30:
            break

