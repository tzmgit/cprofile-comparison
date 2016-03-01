import re
import os
import pstats
from cStringIO import StringIO
from collections import namedtuple, OrderedDict


HEADER_LINE_REGEX = r'ncalls|tottime|cumtime'
STAT_KEYS = ['ncalls', 'tottime', 'tottime_percall', 'cumtime', 'percall']
Stat = namedtuple('Stat', STAT_KEYS)


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


def generate_report(report_file_path, stats, titles=None, stat_source_files=None, export_cols=None):
    col_headers = []
    len_stats = len(stats)
    range_stats = range(len_stats)
    if not titles or len(titles) != len(stats):
        if stat_source_files:
            titles = [os.path.basename(f) for f in stat_source_files]
        else:
            titles = ['stat%d' % (i +1) for i in range_stats]
    export_cols = export_cols or STAT_KEYS
    row_cols = []
    for i, c in enumerate(export_cols):
        col_headers.append(','.join(['{%d}.%s' % (j, c) for j in range_stats]))
        row_cols.append(','.join(['{%d}' % (s * len(export_cols) + i + 1) for s in range_stats]))
    header_template = 'function,' + ','.join(col_headers) + '\n'
    row_template = '{0},' + ','.join(row_cols) + '\n'

    with open(report_file_path, "w") as report:
        report.write(header_template.format(*titles))
        for key, stat in stats[0].iteritems():
            row_vals = [key]
            row_vals.extend([getattr(stat, c) for c in export_cols])
            for tmp_stat in stats[1:]:
                if key in tmp_stat:
                    row_vals.extend([getattr(tmp_stat[key], c) for c in export_cols])
                else:
                    row_vals.extend(['' for _ in export_cols])
            report.write(row_template.format(*row_vals))
    print '\nGenerated report file: %s' % report_file_path


def compare_stats(report_file, stat_source_files, titles=None, stat_filters=None, export_cols=None):
    stats = []
    for stat_file in stat_source_files:
        stats.append(get_stats(stat_file, stat_filters=stat_filters))
    generate_report(report_file, stats, titles=titles, stat_source_files=stat_source_files, export_cols=export_cols)

