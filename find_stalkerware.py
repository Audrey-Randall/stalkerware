import matplotlib
matplotlib.use('Agg')

from matplotlib import pyplot as plt

import subprocess
import re
import time
import numpy as np
import graph_ttls

class DnsResponse:
    status = ''
    opcode = ''
    flags = []
    qtype = ''
    rtt = -1
    ts = ''  # Unix timestamp? todo: python time object
    domain = ''
    ttl = -1
    # Can be CNAME, A, NS, or AAAA afaik
    r_type = ''
    ip = ''

    def extractField(self, line, regex, variable):
        target = ''
        try:
            target = re.search(regex, line).groupdict()[variable]
        except AttributeError:
            print('Regex did not find a match for ' + variable + '. Line = ' + line)
        except KeyError:
            print('No value could be parsed for ' + variable + '. Line = ', line)
        return target

    def printSerialized(self):
        print('Status:' + self.status)
        print('Opcode: ' + self.opcode)
        print('Query type: ' + self.qtype)
        print('RTT: ' + str(self.rtt) + 'ms')
        print('Ts: ' + str(self.ts))
        print('TTL: ' + str(self.ttl))

    def __init__(self, dig_output):
        answer_section = False
        authority_section = False
        lines = dig_output.splitlines()
        for i, line in enumerate(lines):
            if '->>HEADER<<-' in line:
                try:
                    captures = re.search('opcode:\s+(?P<opcode>[A-Z]+),\s+status:\s+(?P<status>[A-Z]+),\s', line).groupdict()
                    self.opcode = captures['opcode']
                    self.status = captures['status']
                except AttributeError:
                    print("Regex did not match in header section. Line = "+line)
                except KeyError:
                    print("No value could be parsed for status and/or opcode. Line = ", line)
                if self.status != 'NOERROR':
                    return
            if 'ANSWER SECTION' in line:
                # This is the line before the answer section.
                answer_section = True
                continue
            if answer_section and line == '':
                answer_section = False
            if answer_section:
                try:
                    # Recall that (?P<name>.*) will put whatever matches the 
                    # pattern after <name> (in this case, .*) into variable name,
                    # which is then accessible in groupdict().
                    captures = re.search("(?P<domain>\S*)\s+(?P<ttl>\d+)\s+IN\s+(?P<record_type>[A-Z])\s+(?P<ip>\S*)", line).groupdict()
                    self.ttl = int(captures['ttl'])
                    self.r_type = captures['record_type']
                    self.domain = captures['domain']
                    self.ip = captures['ip']
                except AttributeError:
                    print("Regex did not match in answer section. Line = "+line)
                except KeyError:
                    print("No value could be parsed for ttl, r_type, ip, and/or domain. Line = ", line)
            if ';; Query time:' in line:
                self.rtt = int(self.extractField(line, ';;\sQuery time: (?P<rtt>\d+).*', 'rtt')) 
            if ';; WHEN:' in line:
                self.ts = self.extractField(line, ';; WHEN:\s+(?P<ts>.*)', 'ts')
             

def makeDigRequest(resolver, target, recursion_desired):
    recurse_flag = '+recurse'
    if resolver[0] != '@':
        resolver = '@' + resolver
    if not recursion_desired:
        recurse_flag = '+norecurse'
    try:
        resp = subprocess.check_output(['dig', resolver, target, recurse_flag])
    except:
        print('Check_output failed for dig')
        return
    return DnsResponse(resp)

    

def aaronsControlledExp(resolver, target):
    # First, put the domain into cache, which should give it its max TTL.
    # holyfamilyhs.com is probably 600
    req1 = makeDigRequest(resolver, target, True)
    if req1.status != 'NOERROR':
        print('Initial dig failed; choose a new domain.')
        return
    max_ttl = req1.ttl

    # Next, see if the TTLs line up with +norecurse.
    ts = []
    ttls = []
    measurement_length = 200
    for i in range(0, measurement_length):
        req = makeDigRequest(resolver, target, False)
        if req.status == 'SERVFAIL':
            time.sleep(1)
            continue
        ts.append(i)
        ttls.append(req.ttl)
        time.sleep(0.5)
    
    if not ttls:
        print('No ttls to plot.')
        return
    unique_intercepts = graph_ttls.calculateTTLLines(ts, ttls)
    print(target, unique_intercepts)
    figname = 'controlled_exp/small_wait/' + target + '.svg'
    graph_ttls.plotTsVsTTLs(np.array(ts), np.array(ttls), 0, measurement_length, max_ttl, target, figname, unique_intercepts)
    
resolver = '8.8.8.8'
# target = 'holyfamilyhs.com'
# aaronsControlledExp(resolver, target)
for d in ['aaronschulman.name', 'holyfamilyhs.com', 'svarka.kz', '95kvartal.business.site', 'bvsd.org']:
    aaronsControlledExp(resolver, d)