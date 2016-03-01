import re
import pstats
from cStringIO import StringIO
from collections import namedtuple, OrderedDict


HEADER_LINE_REGEX = r'ncalls|tottime|cumtime'
Stat = namedtuple('Stat', ['ncalls', 'tottime', 'tottime_percall', 'cumtime', 'percall'])


def get_stats(stat_file, sort='cumtime', stat_filters=None):
    stream = StringIO()
    p = pstats.Stats(stat_file, stream=stream)
    if not isinstance(stat_filters, (list, tuple)):
        stat_filters = [stat_filters]
    p.sort_stats(sort).print_stats(*stat_filters)
    raw_data = stream.getvalue()
    stream.close()
    print raw_data
    data_dict = OrderedDict()
    matched = False
    lines = raw_data.split('\n')
    for l in lines:
        if not matched:
            if re.search(HEADER_LINE_REGEX, l):
                matched = True
                continue
        elif re.match('^\s*$', l):
            print '\nFound stats for %d functions in %s\n' % (len(data_dict), stat_file)
            break
        if matched:
            calls, tottime, tottime_percall, cumtime, percall, function = re.split('\s+', l.strip())
            if '/' in calls:
                calls = calls.partition('/')[0]
            if function in data_dict:
                assert False, 'Found duplicate function: %s' % function
            data_dict[function] = Stat(int(calls), float(tottime), float(tottime_percall), float(cumtime), float(percall))

    return data_dict


def combine_stats(report_file_path, stats1, stats2, title1='stats1', title2='stats2'):
    title1 = title1 or 'stats1'
    title2 = title2 or 'stats2'
    with open(report_file_path, "w") as report:
        report.write(('function,' +
                     '{0}.ncalls,{1}.ncalls,diff.ncalls({1}-{0}),' +
                     '{0}.tottime,{1}.tottime,diff.tottime({1}-{0}),' +
                     '{0}.tottime_percall,{1}.tottime_percall,diff.tottime_percall({1}-{0}),' +
                     '{0}.cumtime,{1}.cumtime,diff.cumtime({1}-{0}),' +
                     '{0}.percall,{1}.percall,diff.percall({1}-{0}),' +
                     '\n').format(title1, title2))
        for key, stat1 in stats1.iteritems():
                if key in stats2:
                    stat2 = stats2[key]
                report.write('{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n'.format(key,
                                                    stat1.ncalls, stat2.ncalls, stat2.ncalls - stat1.ncalls,
                                                    stat1.tottime, stat2.tottime, stat2.tottime - stat1.tottime,
                                                    stat1.tottime_percall, stat2.tottime_percall, stat2.tottime_percall - stat1.tottime_percall,
                                                    stat1.cumtime, stat2.cumtime, stat2.cumtime - stat1.cumtime,
                                                    stat1.percall, stat2.percall, stat2.percall - stat1.percall))
    print '\nGenerated report file: %s' % report_file_path


def compare_stats(stat_file1, stat_file2, report_file, title1=None, title2=None, stat_filters=None):
    d1 = get_stats(stat_file1, stat_filters=stat_filters)
    d2 = get_stats(stat_file2, stat_filters=stat_filters)
    combine_stats(report_file, d1, d2, title1=title1, title2=title2)

