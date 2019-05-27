import base64
import dns.message
import csv
import subprocess

domains = []
def readAlexaDomains(filename):
    with open(filename) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for idx, row in enumerate(readCSV):
            if idx == 0:
                continue
            domains.append(row[1])

def decode():
    dnsmsg = dns.message.from_wire(base64.b64decode('CKuAgAABAAEAAAAACGZhY2Vib29rA2NvbQAAAQABwAwAAQABAAAAtwAEHw1aJA=='))
    print(dnsmsg)

def parseTTLs(filename):
    digFile = open(filename, "r")
    answers = []
    addToArray = False

    # Get the answer lines into an array
    for line in digFile:
        if addToArray and line != "\n" and "CNAME" not in line:
            answers.append(line)
            addToArray = False
        if ";; ANSWER SECTION:" in line:
            addToArray = True
    #print(answers)

    for a in answers:
        aList = a.split()
        print(aList[1])
    print("Items in aList: ", len(answers))

parseTTLs("dig_500_www.txt")


