import re
import json
import builtins


def print(*args, **kwargs):
    kwargs['end'] = ''
    builtins.print(*args, **kwargs)


class Node:
    _re_newline = re.compile('\n+')

    def __init__(self):
        self._has_value = False
        self._text = ''

    def _separator(self):
        return ',' if self._has_value else '{'

    def add_tag(self, tag):
        print('{}"{}":'.format(self._separator(), tag))
        if not self._has_value:
            self._has_value = True

    def add_text(self, text):
        print(json.dumps(text))

    def append_text(self, text):
        self._text += text

    # Adds previously appended text
    def _finish_text(self):
        print(json.dumps(Node._re_newline.sub(' ', self._text)))
        self._text = ''

    def close(self):
        self._finish_text() if self._text else print('}')


class Wiki2Json:
    def __init__(self):
        # One-line key-value
        self._re_one_line = re.compile(r'^\s+<(\w+).*?>(.+)</\1>\s*$')
        # Beginning of a tag and maybe the beginning of its text
        self._re_beg_tag = re.compile(r'^\s+<([^/]\w+).*?>(.*\S.*)?$', re.S)
        # Tag-end regexes will be dynamically generated
        self._re_end_tags = []
        # Only parses 'page' tags
        self._re_beg_page = re.compile(r'^\s+<page>\s*$')
        self._re_end_page = re.compile(r'^\s+</page>\s*$')
        self._re_empty = re.compile(r'^\s+<\w+.*/>')
        self._reset()

    def _reset(self):
        del self._re_end_tags[:]
        # To keep track of separators and endings
        self._parents = [Node()]  # root parent
        self._in_page = False

    def parse_line(self, line):
        # <page>
        if not self._in_page:
            if self._re_beg_page.match(line):
                self._in_page = True
        # </page>
        elif self._re_end_page.match(line):
            self._in_page = False
            print('}\n')
            self._reset()
        # between <page> and </page>
        elif not self._re_empty.match(line):
            self._parse_page(line)

    def _parse_page(self, line):
        m = self._re_one_line.match(line)
        if m:
            # <tag>text</tag>
            self._parent().add_tag(m.group(1))
            self._parent().add_text(m.group(2))
        elif not self._re_empty.match(line):
            self._parse_multiline_tag(line)

    def _parse_multiline_tag(self, line):
        m = self._re_beg_tag.match(line)
        if m:
            # <tag>...
            self._init_multiline_tag(m.group(1))
            if m.group(2):
                self._parent().append_text(m.group(2))
        else:
            m = self._re_end_tags[-1].match(line)
            if m:
                # ...</tag>
                if m.group(1):
                    self._parent().append_text(m.group(1))
                self._end_multiline_tag()
            else:
                # only text, no tags
                self._parent().append_text(line)

    def _init_multiline_tag(self, tag):
        self._parent().add_tag(tag)
        self._parents.append(Node())
        self._add_re_end_tag(tag)

    def _end_multiline_tag(self):
        self._parent().close()
        del self._parents[-1]
        del self._re_end_tags[-1]

    def _add_re_end_tag(self, tag):
        pattern = re.compile('^\s*(\S.*)?</%s>\s*$' % tag)
        self._re_end_tags.append(pattern)

    def _parent(self):
        return self._parents[-1]
