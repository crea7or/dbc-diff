#!/usr/bin/env python3

import os
import cantools
import click
import json
import sys
import datetime
import jinja2
import logging

header = '''
      .:+oooooooooooooooooooooooooooooooooooooo: `/ooooooooooo/` :ooooo+/-`
   `+dCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOEZshCEZEOCEZEOEZ#doCEZEOEZEZNs.
  :CEZEON#ddddddddddddddddddddddddddddddNCEZEO#h.:hdddddddddddh/.yddddCEZEO#N+
 :CEZEO+.        .-----------.`       `+CEZEOd/   .-----------.        `:CEZEO/
 CEZEO/         :CEZEOCEZEOEZNd.    `/dCEZEO+`   sNCEZEOCEZEO#Ny         -CEZEO
 CEZEO/         :#NCEZEOCEZEONd.   :hCEZEOo`     oNCEZEOCEZEO#Ny         -CEZEO
 :CEZEOo.`       `-----------.`  -yNEZ#Ns.       `.-----------.`       `/CEZEO/
  :CEZEONCEZEOd/.ydCEZEOCEZEOdo.sNCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOEZNEZEZN+
   `+dCEZEOEZEZdoCEZEOCEZEOEZ#N+CEZEOCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOCEZEOEZ#s.
      .:+ooooo/` :+oooooooooo+. .+ooooooooooooooooooooooooooooooooooooo+/.

 C E Z E O  S O F T W A R E (c) 2025   DBC diff / compare tool / release notes builder
                        MIT License / pavel.sokolov@gmail.com
'''

fmt_console = '%(levelname)-9s | %(message)s'
fmt_file = fmt_console


class ConsoleFileLogger(logging.getLoggerClass()):
    def __init__(self, name, level, log_file=None):
        super().__init__(name)
        self.setLevel(level)
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.stdout_handler.setLevel(level)
        self.stdout_handler.setFormatter(logging.Formatter(fmt_console))
        self.addHandler(self.stdout_handler)
        self.file_handler = None
        if log_file:
            self.file_handler = logging.FileHandler(log_file)
            self.file_handler.setLevel(level)
            self.file_handler.setFormatter(logging.Formatter(fmt_file))
            self.addHandler(self.file_handler)


class ToolLogger:
    def __init__(self, name, log_file=None):
        self.logger = ConsoleFileLogger(name=name, level=logging.DEBUG, log_file=log_file)

    def debug(self, *args, **kw):
        self.logger.debug(*args, **kw)

    def info(self, *args, **kw):
        self.logger.info(*args, **kw)

    def warning(self, *args, **kw):
        self.logger.warning(*args, **kw)

    def error(self, *args, **kw):
        self.logger.error(*args, **kw)

    def critical(self, *args, **kw):
        self.logger.critical(*args, **kw)
        raise Exception('critical error')


logger = ToolLogger(name="dbc-diff")

message_properties = {
    'frame_id': 'hex',
    'is_extended_frame': 'basic',
    'is_fd': 'basic',
    'length': 'basic',
    'send_type': 'basic',
    'cycle_time': 'basic',
    'senders': 'list',
    'receivers': 'list',
}

signal_properties = {
    'minimum': 'basic',
    'maximum': 'basic',
    'start': 'basic',
    'length': 'basic',
    'byte_order': 'basic',
    'is_signed': 'basic',
    'initial': 'str',
    'invalid': 'basic',
    'unit': 'basic',
    'scale': 'basic',
    'offset': 'basic',
    'is_float': 'basic',
    'choices': 'dict',
    'spn': 'basic',
}


# parse signals into dictionary
def dbc_loader(dbc_file: str):
    messages = {}
    version = None
    if dbc_file is not None:
        dbc = cantools.db.load_file(dbc_file, strict=False)
        for dbc_message in dbc.messages:
            signals = {}
            for signal in dbc_message.signals:
                signals[signal.name] = signal
            setattr(dbc_message, 'msg_signals', signals)
            messages[dbc_message.name] = dbc_message
        version = "unknown" if dbc.version is None or len(dbc.version) == 0 else dbc.version
    return messages, version


def converter(value, from_type):
    if value is None:
        return None
    elif from_type == 'hex':
        return f'{hex(value)}'
    elif from_type == 'str':
        return str(value)
    elif from_type == 'dict':
        result = {}
        for number, name in value.items():
            result[int(number)] = str(name)
        return dict(sorted(result.items()))
    elif from_type == 'list':
        return ','.join(value)
    return value


def compare_dictionaries(old: dict, new: dict) -> {dict, dict, dict}:
    old_set = set(old.keys())
    new_set = set(new.keys())
    same = old_set & new_set
    deleted = old_set - new_set
    added = new_set - old_set
    return sorted(added), sorted(same), sorted(deleted)


def build_change(action, change, signals=None):
    if signals is not None:
        return {'action': action, action: change, 'signals': signals}
    else:
        return {'action': action, action: change}


def build_action(action, item, properties, signals=None):
    properties_list = []
    for item_property, from_type in properties.items():
        value = converter(getattr(item, item_property), from_type)
        if action == 'deleted':
            if value is not None:
                properties_list.append({'name': item_property, 'old': value, 'new': None})
        elif action == 'added':
            if value is not None:
                properties_list.append({'name': item_property, 'old': None, 'new': value})
        else:
            logger.critical(f'unknown action: {action}')
    return build_change(action, properties_list, signals)


def compare_properties(old_object, new_object, properties: dict) -> list:
    changes_list = []
    for name, from_type in properties.items():
        old_property = converter(getattr(old_object, name), from_type)
        new_property = converter(getattr(new_object, name), from_type)
        if old_property != new_property:
            changes_list.append({'name': name, 'old': old_property, 'new': new_property})
    return changes_list


def compare_messages(old_message, new_message):
    message_changes_list = compare_properties(old_message, new_message, message_properties)
    signals_changes = {}
    added, same, deleted = compare_dictionaries(old_message.msg_signals, new_message.msg_signals)
    for name in same:
        changed_list = compare_properties(old_message.msg_signals[name], new_message.msg_signals[name], signal_properties)
        if len(changed_list) > 0:
            signals_changes[name] = build_change('changed', changed_list)
    for name in deleted:
        signals_changes[name] = build_action('deleted', old_message.msg_signals[name], signal_properties)
    for name in added:
        signals_changes[name] = build_action('added', new_message.msg_signals[name], signal_properties)
    return message_changes_list, signals_changes


def message_signals(action: str, signals: dict) -> dict:
    signals_changes = {}
    for name, signal in signals.items():
        signals_changes[name] = build_action(action, signal, signal_properties)
    return signals_changes


def compare_dbc(old_dbc_file_path, new_dbc_file_path) -> {dict, dict}:
    old_dbc, old_version = dbc_loader(old_dbc_file_path)
    new_dbc, new_version = dbc_loader(new_dbc_file_path)
    dbc_report = {}
    versions = {}
    added, same, deleted = compare_dictionaries(old_dbc, new_dbc)
    for name in same:
        message_changed_list, signals_changed_list = compare_messages(old_dbc[name], new_dbc[name])
        if len(message_changed_list) > 0 or len(signals_changed_list) > 0:
            dbc_report[name] = build_change('changed', message_changed_list, signals_changed_list)
    for name in deleted:
        dbc_report[name] = build_action('deleted', old_dbc[name], message_properties, message_signals('deleted', old_dbc[name].msg_signals))
    for name in added:
        dbc_report[name] = build_action('added', new_dbc[name], message_properties, message_signals('added', new_dbc[name].msg_signals))
    if new_dbc_file_path is not None:
        versions['new_version'] = new_version
    if old_dbc_file_path is not None:
        versions['old_version'] = old_version
    versions['same_version'] = old_version == new_version
    return dbc_report, versions


def enum_files(folder: str, file_extension: str) -> dict:
    populated_files = {}
    for current_path, folders, files in os.walk(folder):
        for file in files:
            if file.endswith(file_extension):
                file_path = os.path.join(current_path, file)
                if file in populated_files.keys():
                    logger.error(f'error: same DBC file found more than once: {populated_files[file]} and {file_path}')
                populated_files[file] = file_path
    return populated_files


def write_json_report(json_output: str, data: dict) -> str:
    if not json_output.endswith('.json'):
        json_output += '.json'

    with open(json_output, 'w', encoding="utf-8") as out_file:
        out_file.truncate()
        out_file.write(json.dumps(data))

    return json_output


def get_report(old_files: dict[str, str], new_files: dict[str, str], unchanged: bool) -> dict:
    compare_report = {}
    added, same, deleted = compare_dictionaries(old_files, new_files)
    for file_added in added:
        dbc_report, versions = compare_dbc(None, new_files[file_added])
        compare_report[file_added] = build_change('added', dbc_report) | versions
    for file_deleted in deleted:
        dbc_report, versions = compare_dbc(old_files[file_deleted], None)
        compare_report[file_deleted] = build_change('deleted', dbc_report) | versions
    for file_same in same:
        dbc_report, versions = compare_dbc(old_files[file_same], new_files[file_same])
        if len(dbc_report) > 0 or not versions['same_version']:
            compare_report[file_same] = build_change('changed', dbc_report) | versions
        elif unchanged:
            compare_report[file_same] = build_change('unchanged', dbc_report) | versions
    return compare_report


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def get_script_name():
    return os.path.splitext(os.path.basename(os.path.realpath(sys.argv[0])))[0]


def generate_from_template(template_name, template_params, generated_output_path):
    jinja_loader = jinja2.FileSystemLoader(get_script_path())
    environment = jinja2.Environment(loader=jinja_loader, trim_blocks=True, lstrip_blocks=True)
    template = environment.get_template(template_name)
    content = template.render(template_params)
    with open(generated_output_path, 'w', encoding="utf-8") as out_file:
        out_file.truncate()
        out_file.write(content)
        logger.info(f"Report generated successfully: {generated_output_path}")


@click.command(context_settings={"ignore_unknown_options": True})
@click.option('--old', '--from', '-f', required=True, type=click.Path(exists=True), help="Path to folder(file) with old file(s)")
@click.option('--new', '--to', '-t', required=True, type=click.Path(exists=True), help="Path to folder(file) with new file(s)")
@click.option('--unchanged', '-u', required=False, default=False, is_flag=True, help="Include DBCs that are not changed")
@click.option('--reports', '-r', required=True, type=str, help=f"Create specified reports from templates, list of types delimited by comma (json,html,md ...)")
@click.option('--info', '-i', help="Additional info to display in report (about report)")
@click.option('--name', '-n', required=False, type=str, help="Report base file name, reports will be created with: <name>.json, <name>.html... etc.")
@click.option('--output', '-o', required=False, type=click.Path(exists=True), help="Report output folder name")
def main(old: str, new: str, unchanged: bool, reports: str, info: str, name: str, output: str ):

    print(header)

    old_file_name = None
    if os.path.isdir(old):
        old_files = enum_files(old, '.dbc')
    elif os.path.isfile(old):
        old_file_name = os.path.basename(old)
        old_files = {old_file_name: old}
    else:
        raise ValueError(f'Unknown source: {old}')

    if os.path.isdir(new):
        new_files = enum_files(new, '.dbc')
    elif os.path.isfile(new):
        new_file_name = os.path.basename(new)
        # compare different filenames need a fix
        if old_file_name is not None and old_file_name != new_file_name:
            new_file_name = old_file_name + ' -> ' + new_file_name
            old_files[new_file_name] = old_files.pop(old_file_name)
        new_files = {new_file_name: new}
    else:
        raise ValueError(f'Unknown source: {new}')

    compare_report = get_report(old_files, new_files, unchanged)

    report_name = get_script_name() if name is None else name
    report_path = get_script_path() if output is None else output
    reports_list = reports.split(',')
    for report_tag in reports_list:
        report_extension = report_tag.strip(' \n\r\t')

        report_save_path = os.path.join(report_path, f'{report_name}.{report_extension}')
        template_name = f'{get_script_name()}.{report_extension}.jinja2'
        template_path = os.path.join(get_script_path(), template_name)

        if report_extension == 'json':
            result = write_json_report(report_save_path, compare_report)
            logger.info(f"Report saved: {result}")
        else:
            if info is None:
                info = datetime.datetime.now()
            if not os.path.exists(template_path):
                raise FileNotFoundError(f'Report template "{template_name}" is not found')
            generate_from_template(template_name, {'dbc_files': compare_report, 'build_info': info}, report_save_path)


if __name__ == '__main__':
    main()
