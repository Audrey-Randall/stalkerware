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
    unique_intercepts = []
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
    unique_intercepts.append(intercepts[0])
    for i in range(0, len(intercepts)-1):
        if intercepts[i] != intercepts[i+1]:
            unique_intercepts.append(intercepts[i+1])
    print("Total intercepts: " + str(len(intercepts)))
    return np.array(unique_intercepts)

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

def sortByDomain(ttls_by_domain, ts_by_domain, max_ttls_by_domain):
    start_ts = query_results["ts"][0]
    for i, d in enumerate(query_results["domain"]):
        if d not in ttls_by_domain:
            ttls_by_domain[d] = []
            ts_by_domain[d] = []
            max_ttls_by_domain[d] = 0
        else:
            ts_by_domain[d].append(query_results["ts"][i] - start_ts)
            ttl = query_results["ttls"][i]
            ttls_by_domain[d].append(ttl)
            if ttl > max_ttls_by_domain[d]:
                max_ttls_by_domain[d] = ttl
    for d in ts_by_domain:
        # Assume in most cases that the max TTL we see is one less than the actual TTL:
        # for example, if we see a largest TTL of 59, the max TTL will be 60. This 
        # relies on the assumption that our measurements have been occurring long enough
        # to see the highest TTL. 
        max_ttls_by_domain[d] = max_ttls_by_domain[d]+ 1

def plotReplicasOverTime(domain, unique_intercepts, start_time, end_time, max_ttl, scale_ttls=False):
    # Given the set of y-intercepts of all the TTL lines, plot the number of replicas 
    # active at a time.
    lowest_intercept_idx = 0
    active_replicas = []
    # end_time + 1 so that if you're graphing one TTL segment, you get a line.
    time_intervals = np.arange(start_time, end_time + 1, max_ttl)
    ttl_scaling_factor = 1.0
    if scale_ttls:
        ttl_scaling_factor = 60.0 / float(max_ttl)
    print(time_intervals)
    for t in time_intervals:
        # Let y_int be the y-intercept of the TTL line.
        # The relevant TTL lines at time t will have intercepts between y=t and y=t + max_ttl,
        # because the slope is -1.
        low_bound = t
        high_bound = t + max_ttl

        # Get the intercepts that are between the bounds
        active_ttl_line_idxs = np.where(np.logical_and(unique_intercepts > low_bound, unique_intercepts < high_bound))[0]
        active_replicas.append(len(active_ttl_line_idxs) * ttl_scaling_factor)

    plt.plot(time_intervals - start_time, active_replicas)
    plt.xlim(0, end_time - start_time)
    figname = 'kim_results/popular/active_replicas/' + domain
    if scale_ttls:
        figname += '_adjusted_active_replicas.png'
    else:
        figname += '_active_replicas.png'
    xlabel = "Timestamp (seconds since " + str(start_time) +"). TTL = " + str(max_ttl)
    plt.xlabel(xlabel)
    plt.ylabel("Number of active replicas")
    title = "Active replicas for " + domain
    plt.title(title)
    plt.savefig(figname)
    plt.show()
    plt.close()

def performAnalysis(results_file):
    ttls_by_domain = {}
    ts_by_domain = {}
    max_ttls_by_domain = {}
    
    # Read the result file from Kim and record data by column.
    readFindStalkerwareResults(results_file)
    
    # Separate out data by domain.
    sortByDomain(ttls_by_domain, ts_by_domain, max_ttls_by_domain)

    for d in ts_by_domain:
        # Normalize the timestamps so they start at 0, and convert everything to ndarrays
        first_ts = ts_by_domain[d][0]
        np_ts = np.array(ts_by_domain[d]) - first_ts
        np_ttls = np.array(ttls_by_domain[d])

        # Determine how many unique TTL lines exist.
        unique_intercepts = calculateTTLLines(np_ts, np_ttls)

        max_ttl = max_ttls_by_domain[d]
        start_time = max_ttl * 4
        # end_time = 20 * max_ttl + start_time
        end_time = max_ttl * 5
        time_interval = end_time - start_time

        # Plot the number of active replicas per TTL over the course of the second day of measurements
        plotReplicasOverTime(d, unique_intercepts, 60*60*24, 60*60*24*2, max_ttl)

        # Determine what range of points to display to easily see the TTL lines.
        idx_range = np.where(np.logical_and(np_ts >= start_time, np_ts <= end_time))[0]
        intercept_range = np.where(np.logical_and(unique_intercepts < end_time + time_interval, unique_intercepts >= start_time))[0]

        # Get the chunks of the arrays to plot, and plot them.
        ts_in_range = np_ts[idx_range]
        ttls_in_range = np.array(ttls_by_domain[d])[idx_range]
        np_intercepts_in_range = unique_intercepts[intercept_range]
        print("np_intercepts: ", np_intercepts_in_range)
        for i in range(0, len(ts_in_range)):
            print(ts_in_range[i], ttls_in_range[i])
        
        plotTsVsTTLs(ts_in_range, ttls_in_range, start_time, end_time, max_ttl, d, np_intercepts_in_range)

def plotTsVsTTLs(ts, ttls, start, end, max_ttl, domain, unique_intercepts=[]):
    plt.xlim(0, end-start)
    plt.ylim(0, max_ttl)
    for i in unique_intercepts:
        plt.plot([i - max_ttl - start, i - start], [max_ttl, 0], linewidth=0.5)
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
    figname = 'kim_results/popular/ttls_with_lines/' + domain + '_ttls.png'
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


# def plotTsVsTTLs(start, end, filename):
#     plt.plot(query_results['ts'][start:end], query_results['ttls'][start:end], linestyle="",marker="o", markersize=2.0)
#     plt.grid(axis='x', linewidth=0.5, linestyle = 'dashed', which='minor')
#     #plt.xticks(np.arange(start, end, 300))
#     plt.xticks(np.arange(int(query_results['ts'][start]), int(query_results['ts'][end]), end-start), which='minor')
#     plt.xlabel('Timestamp (seconds since first timestamp)')
#     plt.ylabel('TTL (seconds)')
#     title = 'TTL lines for ' + str(int(query_results['ts'][start])) + ' seconds to ' + str(int(query_results['ts'][end])) + ' seconds'
#     plt.title(title)
#     figname = filename.split('.')[0] + '_' + str(start) + '_' + str(end) + '.png'
#     plt.savefig(figname)
#     plt.show()

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
performAnalysis("kim_results/kim_results_popular_10-1-2019.txt")