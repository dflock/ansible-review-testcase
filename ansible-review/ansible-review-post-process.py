"""
Post process the output from Ansible Review.

This script runs Ansible Review, captures the output, then
post-processes it into a Github formated markdown Checklist, which
it then outputs to stdout.

It uses the blessed module for output, so it has nice formatting
in the console, but is pipe aware, so you don't get control chars
in piped output.
"""

import os
import re
import subprocess

from blessed import Terminal
from operator import itemgetter


# DEBUG/TEST: don't run the command, it's slow, just suck in
# a pre-grenerated text file of the output
# with open(os.path.expanduser('~/tmp/ansible-review-output-collapsed.txt'), 'r') as f:
#     output = f.readlines()

# Get the output from ansible-review, and collapse the two-line output into one line:
# when a line ends in `met:`, the next line is a continuation, so collapse into one line
# Skip group_vars - this outputs a non-standard msg about inventory file being broken
# see here: https://github.com/willthames/ansible-review/issues/21
cmd = r"git ls-files ansible/. | grep -v group_vars | xargs ansible-review 2>/dev/null | sed -n '/met:/ {N; s/[\r\n]/ /g; p}'"

try:
    output = subprocess.check_output(
        cmd,
        stderr=subprocess.STDOUT,
        shell=True
    ).split('\n')
except subprocess.CalledProcessError as e:
    output = e.output.split('\n')

t = Terminal()
output_lines = []

# print output

class WarningLine:
    regex = r'^WARN: (.*) not met: (.*?):(.*?): (.*)$'
    text, filename, line, rule = range(1, 5)


for line in output:
    # print line
    # Convert the string line into an output_item dict, then add
    # it to the output_lines list.
    if line.startswith('WARN: '):
        # It's a warning item
        match = re.search(WarningLine.regex, line)
        # print len(match.groups())
        if match and len(match.groups()) == 4:
            output_lines.append({
                'log_level': t.yellow('WARN'),
                'file': match.group(WarningLine.filename),
                'line': int(match.group(WarningLine.line)),
                'text': match.group(WarningLine.text),
                'rule': match.group(WarningLine.rule),
            })

# print len(output_lines)

# The output from ansible-review is sorted by filename, but it's nicer
# if we sort it by filename & line_no
sorted_output = sorted(output_lines, key=itemgetter('file', 'line'))

#
# Print the output_lines list, to the console, in markdown format
#
print(t.dim('# ') + t.bold('Ansible Review Checklist'))

curr_file = ''

for line in sorted_output:
    if line['file'] != curr_file:
        curr_file = line['file']
        print(t.dim('\n## ') + t.bold(curr_file))

    print t.dim('- []') + ' {l[log_level]}: Line: {l[line]:>3}: {l[text]}, rule: {l[rule]}'.format(l=line)
