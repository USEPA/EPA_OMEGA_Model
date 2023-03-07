# Python program to read CSV file line by line
# import necessary packages
import csv

ld_cars = ["CONVERTIBLE", "HATCHBACK", "SEDAN", "WAGON"]
ld_trucks = ["PICKUP SPORT UTILITY", "PICKUP UNKNOWN", "PICKUP VAN", "SPORT UTILITY TRUCK",\
             "SPORT UTILITY VEHICLE", "VAN CAMPER"]
md_trucks = ["BUS NON SCHOOL", "CAB CHASSIS", "COMMERCIAL CHASSIS", "CUTAWAY",\
             "INCOMPLETE (STRIP CHASSIS)", "INCOMPLETE PICKUP", "MOTOR HOME",\
             "STEP VAN", "STRAIGHT TRUCK"]
mixed_trucks = ["PICKUP", "PICKUP CONVENTIONAL", "PICKUP CREW CAB", "PICKUP EXTENDED CAB", "VAN CARGO",\
                "VAN PASSENGER"]

# Open file
with open('D:/Polk/epa_vmt_202301.csv') as file_obj:
    # Create reader object by passing the file
    # object to reader method
    reader_obj = csv.reader(file_obj)

    # Iterate over each row in the csv
    # file using reader object
    state = "CALIFORNIA"
    model_year = "2023"
    make = "DODGE"
    model = "JOURNEY"
    a = 0
    b = 0
    for row in reader_obj:
        a = a + 1
        if a == 3000000:
            break
        if row[0] == state and row[1] == model_year and row[2] == make and row[3] == model:
            print(row)

