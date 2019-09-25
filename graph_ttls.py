import matplotlib
matplotlib.use('Agg')

import csv
from matplotlib import pyplot as plt
import numpy as np

query_results = {}
map_idx_to_column = {}

'''
Assumes the csv is generated by Hive. 
Can have any number of columns but must include 'ttls' and 'ts'
Assumes table name is prepended to column name
'''
def readHiveResultFile(filename):
    with open(filename) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for idx, row in enumerate(readCSV):

            # Get the column names and strip off the table name
            if idx == 0:
                for i, item in enumerate(row):
                    strippedName = item.split('.')[1]
                    query_results[strippedName] = []
                    map_idx_to_column[i] = strippedName
                continue

            # Store items in appropriate columns
            for i, item in enumerate(row):
                colName = map_idx_to_column[i]
                if colName == 'ts':
                    if idx == 1:
                        start_ts = float(item)
                    query_results[colName].append(float(item) - start_ts)
                elif colName == 'ttls':
                    query_results[colName].append(float(item))
                else:
                    query_results[colName].append(item)

'''
Reads the result file generated by find_stalkerware.sh. No column headers:
columns are DNS query type, domain, TTL, timestamp.
'''
def readFindStalkerwareResults(filename):
    with open(filename) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        # Assign the column names
        columns = ["query_type", "domain", "ttls", "ts"]
        for i, c in enumerate(columns):
            query_results[c] = []
        missingValues = 0
        
        for linenum, row in enumerate(readCSV):
            # Store items in appropriate columns
            for i, item in enumerate(row):
                colName = columns[i]
                if colName == 'ts' or colName == "ttls":
                    try:
                        test = int(item)
                    except:
                        # Keep track of how many missing data there are.
                        missingValues += 1

                        # Erase this record from the data by deleting 
                        # any other elements in the row that have already 
                        # been recorded.
                        query_results["query_type"].pop()
                        query_results["domain"].pop()
                        if colName == "ts":
                            query_results["ttls"].pop()
                        continue
                    query_results[colName].append(int(item))
                else:
                    query_results[colName].append(item)
        print("Missing values: " + str(missingValues))
        return missingValues

def calculateTTLLines(timestamps, ttls):
    intercepts = []
    unique_intercepts = 0
    for idx, ttl in enumerate(ttls):
        ts = timestamps[idx]

        # Calculate the intercept. Slope is always -1, so if y1 = ttl and x1 = ts:
        # y = y1 = m(x - x1)
        # y - y1 = x1 - x
        # y = x1 + y1 + 0 
        #   = x1 + y1
        intercept = ts + ttl
        intercepts.append(intercept)
    # Figure out how many unique intercepts there are
    intercepts.sort()
    for i in range(0, len(intercepts)-1):
        if intercepts[i] != intercepts[i+1]:
            unique_intercepts += 1
    if intercepts[-1] != intercepts[-2]:
        unique_intercepts += 1
    print("Total intercepts: " + str(len(intercepts)))
    return unique_intercepts

def getPointRange(start_time, end_time, ts):
    # Take the first index where the timestamp is larger than the start time,
    # and the last index where the timestamp is smaller than the end time.
    # Works because the timestamps are sorted.
    start_idx = 0
    end_idx = len(ts)
    start_idxs = np.where(ts >= start_time)[0]
    if len(start_idxs) != 0:
        start_idx = start_idxs[0]
    end_idxs = np.where(ts > end_time)[0]
    if len(end_idxs) != 0:
        end_idx = end_idxs[0]
    return np.arange(start_idx, end_idx, 1)

def sortByDomain():
    readFindStalkerwareResults("kim_results/kim_results_9-24-19.txt")
    ttls_by_domain = {}
    ts_by_domain = {}
    max_ttls_by_domain = {}
    for i, d in enumerate(query_results["domain"]):
        if d not in ttls_by_domain:
            ttls_by_domain[d] = []
            ts_by_domain[d] = []
            max_ttls_by_domain[d] = 0
        else:
            ts_by_domain[d].append(query_results["ts"][i])
            ttl = query_results["ttls"][i]
            ttls_by_domain[d].append(ttl)
            if ttl > max_ttls_by_domain[d]:
                max_ttls_by_domain[d] = ttl
    for d in ts_by_domain:
        max_ttl = max_ttls_by_domain[d]+ 1
        # Normalize the timestamps and convert to numpy array.
        np_ts = np.array(ts_by_domain[d])
        np_ts = np_ts - np_ts[0]

        # Determine how many unique TTL lines exist.
        unique_intercepts = calculateTTLLines(np_ts, np.array(ttls_by_domain[d]))
        print("Unique intercepts for " + d + ": " + str(unique_intercepts))

        # Determine what range of points to display to easily see the TTL lines.
        start_time = 864000
        end_time = 20 * max_ttl + start_time
        idx_range = getPointRange(start_time, end_time, np_ts)

        # Get the chunks of the arrays to plot, and plot them.
        ts_in_range = np_ts[idx_range]
        ttls_in_range = np.array(ttls_by_domain[d])[idx_range]
        plotTsVsTTLs(ts_in_range, ttls_in_range, start_time, end_time, max_ttl, d)

'''
Assumes the csv looks like this:

response_time, ttl
6, 255
6, 201

csv files like this are generated by timing_attack.sh
'''
def readDigResults(filename):
    with open(filename) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        map_column_to_idx = {}
        for idx, row in enumerate(readCSV):

            # Get the column names and strip off the table name
            if idx == 0:
                print(row)
                for i, name in enumerate(row):
                    map_idx_to_column[i] = name
                    map_column_to_idx[name] = i
                    query_results[name] = []
                continue

            # Horrible hack for separating servers
            resp_col = map_column_to_idx['response_time']
            if int(row[resp_col]) < 20:
                continue

            # Store items in appropriate columns
            for i, item in enumerate(row):
                colName = map_idx_to_column[i]
                query_results[colName].append(int(item))


def plotTsVsTTLs(start, end, filename):
    plt.plot(query_results['ts'][start:end], query_results['ttls'][start:end], linestyle="",marker="o", markersize=2.0)
    plt.grid(axis='x', linewidth=0.5, linestyle = 'dashed', which='minor')
    #plt.xticks(np.arange(start, end, 300))
    plt.xticks(np.arange(int(query_results['ts'][start]), int(query_results['ts'][end]), end-start), which='minor')
    plt.xlabel('Timestamp (seconds since first timestamp)')
    plt.ylabel('TTL (seconds)')
    title = 'TTL lines for ' + str(int(query_results['ts'][start])) + ' seconds to ' + str(int(query_results['ts'][end])) + ' seconds'
    plt.title(title)
    figname = filename.split('.')[0] + '_' + str(start) + '_' + str(end) + '.png'
    plt.savefig(figname)
    plt.show()

def plotTsVsTTLs(ts, ttls, start, end, max_ttl, domain):
    plt.plot(ts - start, ttls, linestyle="",marker="o", markersize=2.0)
    plt.grid(axis='x', linewidth=0.5, linestyle = 'dashed', which='minor')
    plt.xticks(np.arange(0, end-start, max_ttl))
    plt.axes().xaxis.set_major_locator(plt.MaxNLocator(10))
    plt.axes().xaxis.set_minor_locator(plt.MaxNLocator(20))
    xlabel = 'Timestamp (seconds after ' + str(start) +'s)'
    plt.xlabel(xlabel)
    plt.ylabel('TTL (seconds)')
    title = 'TTL lines for ' + domain
    plt.title(title)
    figname = 'kim_results/kim_result_graphs/' + domain + '_ttls.png'
    plt.savefig(figname)
    plt.show()
    plt.close()

def plotRespTimeVsTTLs():
    plt.plot(query_results['response_time'], query_results[' ttl'], linestyle="",marker="o", markersize=2.0)
    plt.xlabel('Response time (ms)')
    plt.ylabel('TTL (seconds)')
    title = 'TTLs vs response times: query for facebook.com to 8.8.8.8,\n recursion desired'
    plt.title(title)
    figname = 'resp_time_vs_ttl_facebookcom.png'
    plt.savefig(figname)
    plt.show()

def plotWallTimeVsTTLs():
    plt.plot(query_results[' time_elapsed'], query_results[' ttl'], linestyle="",marker="o", markersize=2.0)
    plt.xlabel('Time elapsed (seconds)')
    plt.ylabel('TTL (seconds)')
    title = 'TTLs vs time elapsed: query for facebook.com to 8.8.8.8,\n recursion desired'
    plt.title(title)
    #figname = 'wall_time_vs_ttl_facebookcom.png'
    #plt.savefig(figname)
    plt.show()

def makeHiveGraph(filename):
    readHiveResultFile()
    plotTsVsTTLs()

def makeDigGraph(filename):
    readDigResults(filename)
    #plotRespTimeVsTTLs()
    print(query_results['response_time'])
    plotWallTimeVsTTLs()

# filename = "bash_scripts/timing_attack_rate_limited.csv"
# makeDigGraph(filename)
sortByDomain()