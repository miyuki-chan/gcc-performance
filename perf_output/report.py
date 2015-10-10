import re

class ReportError(Exception): pass

def error(msg):
    raise ReportError(msg)

def to_num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)

class ReportLine:
    def __init__(self, line, separator):
        data = line.split(separator)
        if len(data) < 3:
            error('Failed to parse: '+line)
        if data[0] in ['<not counted>', '<not supported>']:
            self.name = None
            self.value = None
            return
        self.name = data[2]
        if self.name.endswith(':HG'):
            self.name = self.name[:-3]

        try:
            self.value = to_num(data[0])
        except:
            error('Failed to parse number \'{}\' in \'{}\''.format(data[0], line))
        if len(data) == 4:
            if data[3][-1] != '%':
                error('Invalid stddev \'{}\' in \'{}\''.format(data[3], line))
            percent = data[3][:-1]
            try:
                self.stddev = to_num(percent) / 100
            except:
                error('Failed to parse number \'{}\' in \'{}\''.format(percent, line))
        else:
            self.stddev = None
    
    def __str__(self):
        res = '{}: {}'.format(self.name, self.value)
        if self.stddev is not None:
            res += ' ({:.2f} %)'.format(self.stddev * 100)
        return res

class RunReport:
    def __init__(self, name, lines, separator):
        self.values = {}
        self.name = name
        self.cycles = None
        self.insns = None
        self.task_clock = None
        for line in lines:
            rep_line = ReportLine(line, separator)
            if rep_line.name is None:
                continue
            self.values[rep_line.name] = rep_line
            if rep_line.name == 'cycles':
                self.cycles = rep_line
            elif rep_line.name == 'instructions':
                self.insns = rep_line
            elif rep_line.name == 'task-clock':
                self.task_clock = rep_line

    def keys(self):
        return self.values.keys()
    
    def __repr__(self):
        res = '<RunReport '
        if self.name is not None:
            res += self.name + ' '
        return res + ', '.join(str(v) for v in self.values.values()) + '>'

    def __getitem__(self, key):
        return self.values[key]

    def __contains__(self, key):
        return key in self.values

    @property
    def have_stddev(self):
        return self.values.values()[0].stddev is not None

class PerfReport:
    WORKLOAD_RE = re.compile(r'^\s*#\s*WORKLOAD:\s*(.*?)\s*$')

    def __init__(self, input, separator=','):
        class RunReportBuilder:
            def __init__(self):
                self.lines = []
                self.workload_name = None

            def append_line(self, line):
                self.lines.append(line)

            def maybe_flush(self, dest):
                if not self.lines:
                    return                
                dest.append(RunReport(self.workload_name, self.lines, separator))
                self.lines = []
                self.workload_name = None

        self.runs = []
        bld = RunReportBuilder()

        for line in input:
            match = self.WORKLOAD_RE.match(line)
            if match:
                bld.maybe_flush(self.runs)
                bld.workload_name = match.group(1)
                continue
            pos = line.find('#')
            if pos >= 0:
                line = line[:pos]
            line = line.strip()
            if not line:
                bld.maybe_flush(self.runs)
                continue
            bld.append_line(line)
        bld.maybe_flush(self.runs)

    def __str__(self):
        return str(self.runs)
            
    def __getitem__(self, ind):
        return self.runs[ind]

    def __len__(self):
        return len(self.runs)
    
    def get_raw_data(self):
        result = []
        for run in self.runs:
            row = {'name': run.name}
            for k, v in run.values.items():
                row[k] = v.value
                if v.stddev is not None:
                    row[k + '-stddev'] = v.stddev
            result.append(row)
        return result

    @property
    def empty(self):
        return len(self.runs) == 0