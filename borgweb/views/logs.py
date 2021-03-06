"""
logs view
"""

import os

from flask import current_app, render_template, jsonify

from . import blueprint

SUCCESS, INFO, WARNING, DANGER = 'success', 'info', 'warning', 'danger'


def overall_classifier(f):
    # TODO: we need sane logging with log levels, sane return codes, logging
    #       of return codes in Borg before this can be really useful.
    # we expect the most interesting stuff at the end of the log file:
    end = f.seek(0, os.SEEK_END)
    f.seek(max(0, end - 1024), os.SEEK_SET)
    lines = [line.rstrip('\n') for line in f.readlines()]
    f.seek(0, os.SEEK_SET)
    classifications = set([line_classifier(line) for line in lines[1:]])
    for cls in DANGER, WARNING, SUCCESS:
        if cls in classifications:
            return cls
    return DANGER  # something strange happened (empty log?)


def line_classifier(line):
    # TODO: we need sane logging with log levels, sane return codes, logging
    #       of return codes in Borg before this can be really useful.
    if line.startswith('borg: Exiting with failure status due to previous errors'):
        return DANGER
    if line.startswith('borg: '):
        return WARNING
    return SUCCESS


def _get_logs():
    log_dir = current_app.config['LOG_DIR']
    log_dir = os.path.abspath(log_dir)
    try:
        log_files = os.listdir(log_dir)
    except OSError:
        log_files = []
    return log_dir, sorted(log_files, reverse=True)


def _get_log_lines(log_dir, log_file, offset, linecount=None, direction=1):
    log_file = os.path.join(log_dir, log_file)
    with open(log_file, 'r') as f:
        if direction == 1:  # forwards
            f.seek(offset)
            if linecount is None:  # read all, starting from offset
                log_lines = f.readlines()
            else:  # read n lines, starting from offset
                log_lines = []
                for i in range(linecount):
                    line = f.readline()
                    if not line:
                        break
                    log_lines.append(line)
            offset = f.tell()
        elif direction == -1:  # backwards
            log_lines = []
            if linecount is None:  # read all, up to offset
                start = 0
            else:  # read n lines, up to offset
                # we do not expect medium line length bigger than 1024
                start = max(0, offset - linecount * 1024)
            f.seek(start)
            current = 0
            while current < offset:
                line = f.readline()
                if not line:
                    break
                current = f.tell()
                log_lines.append((current, line))
            if linecount is None:
                offset = 0
                log_lines = [line for _, line in log_lines]
            else:
                try:
                    offset = log_lines[-linecount-1][0]
                except IndexError:
                    offset = 0
                log_lines = [line for _, line in log_lines[-linecount:]]
        else:
            raise ValueError("give direction == 1 (forwards) or -1 (backwards)")
        log_lines = [line.rstrip('\n') for line in log_lines]
    return log_file, offset, log_lines


@blueprint.route('/logs/<int:index>/<offset>:<linecount>:<direction>')
def get_log_fragment(index, offset, linecount, direction):
    try:
        offset = int(offset)
    except ValueError:
        offset = 0
    try:
        linecount = int(linecount)
    except ValueError:
        linecount = None
    try:
        direction = int(direction)
        if direction not in (-1, 1):
            raise ValueError
    except ValueError:
        direction = 1
    log_dir, log_files = _get_logs()
    try:
        log_file = log_files[index]
    except IndexError:
        log_file = ''
    if log_file:
        log_file, offset, log_lines = _get_log_lines(log_dir, log_file, offset, linecount, direction)
    else:
        log_lines = []
    log_lines = [(line_classifier(line), line) for line in log_lines]
    return jsonify(dict(lines=log_lines, offset=offset))


@blueprint.route('/logs/<int:index>')
def get_log(index):
    log_dir, log_files = _get_logs()
    try:
        log_file = log_files[index]
    except IndexError:
        log_file = ''
    else:
        log_file = os.path.join(log_dir, log_file)
    with open(log_file, 'r') as f:
        length = f.seek(0, os.SEEK_END)
        status = overall_classifier(f)
    return jsonify(dict(filename=log_file, status=status, length=length))


@blueprint.route('/logs')
def get_logs():
    log_dir, log_files = _get_logs()
    return jsonify(dict(dir=log_dir,
                        files=list(enumerate(log_files))))
