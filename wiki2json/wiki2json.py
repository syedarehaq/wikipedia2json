import re
import json
import builtins
from io import StringIO
from datetime import datetime
import time


# Do not print extra newline
def print(*args, **kwargs):
    kwargs['end'] = ''
    builtins.print(*args, **kwargs)


class Node:
    def __init__(self):
        self._has_value = False
        self._text = StringIO()

    def _separator(self):
        return ',' if self._has_value else '{'

    def add_tag(self, tag, opening_another_revision=False):
        if not opening_another_revision:
            if tag == "revision":
                print('{}"revisions":'.format(self._separator(), tag))
            else:
                print('{}"{}":'.format(self._separator(), tag))
        else:
            print('{}'.format(self._separator()))
        if not self._has_value:
            self._has_value = True

    def add_value(self, value):
        print(json.dumps(value))

    def append_multiline_text(self, text):
        self._text.write(text)

    def add_timestamp(self, iso):
        ## Syed change
        #local = datetime.strptime(iso, '%Y-%m-%dT%H:%M:%SZ').timestamp()
        #utc = local - time.timezone
        #print(int(utc))
        print(json.dumps(iso))

    # Adds previously appended text
    def _finish_multiline_text(self):
        ## Syed Change, he wants to keep the newlines in the text.
        #print(json.dumps(self._text.getvalue().replace('\n', ' ')))
        print(json.dumps(self._text.getvalue()))
        self._text.seek(0)

    def close(self,tag):
        #import code; code.interact(local=dict(globals(), **locals()))
        ## Syed dubugged here to resolve an issue where a multiline empty
        ## text was producing an unclosed }
        """
        <revision>
      <id>36442</id>
      <parentid>26027</parentid>
      <timestamp>2002-03-08T23:34:12Z</timestamp>
      <contributor>
        <username>Eclecticology</username>
        <id>372</id>
      </contributor>
      <comment>*</comment>
      <model>wikitext</model>
      <format>text/x-wiki</format>
      <text xml:space="preserve">
</text>
      <sha1>lsg218ik67gsxdgv7qo53f5djrsmhif</sha1>
    </revision>
        """
        if tag in ["text","comment"]:
            self._finish_multiline_text() if self._text.tell() > 0 else print(json.dumps(self._text.getvalue()))
        else:
            self._finish_multiline_text() if self._text.tell() > 0 else print('}')


class Wiki2Json:
    def __init__(self):
        # One-line key-value
        self._re_one_line = re.compile(r'\s+<(\w+).*?>(.+)</\1>')
        # Beginning of a tag and maybe the beginning of its text
        self._re_beg_tag = re.compile(r'\s+<([^/]\w+).*?>(.*\S.*)?', re.S)
        # Tag-end regexes will be dynamically generated
        self._re_end_tags = []
        # Only parses 'page' tags
        self._re_beg_page = re.compile(r'\s+<page>')
        self._re_end_page = re.compile(r'\s+</page>')
        self._re_empty = re.compile(r'\s+<(\w+).*/>')
        self._opened_revision_arr = False
        self._previous_multiline_tag = None
        self._current_multiline_tag = None
        self._reset()

    def _reset(self):
        del self._re_end_tags[:]
        # To keep track of separators and endings
        self._parents = [Node()]  # root parent
        self._in_page = False

    def parse_line(self, line):
        #import code; print(line); code.interact(local=dict(globals(), **locals()))
        # <page>
        if not self._in_page:
            if self._re_beg_page.match(line):
                self._in_page = True
        # </page>
        elif self._re_end_page.match(line):
            self._in_page = False
            self._opened_revision_arr = False
            self._previous_multiline_tag = None
            self._current_multiline_tag = None
            print(']}\n')
            self._reset()
        # between <page> and </page>
        else:
            m = self._re_empty.match(line)
            # contributor as True messes the json schema inferred by Spark
            if m and m.group(1) != 'contributor':
                self._parent().add_tag(m.group(1))
                self._parent().add_value("TRUE")
            elif not m:
                self._parse_page(line)

    def _parse_page(self, line):
        m = self._re_one_line.match(line)
        if m:
            # <tag>text</tag>
            self._parent().add_tag(m.group(1))
            tag, value = m.group(1), m.group(2)
            if tag.endswith('id') or tag == 'ns':
                self._parent().add_value(int(value))
            elif tag == 'timestamp':
                ## Syed change, I will keep the iso date
                self._parent().add_timestamp(value)
            else:
                self._parent().add_value(value)
        else:
            self._parse_multiline_tag(line)

    def _parse_multiline_tag(self, line):
        m = self._re_beg_tag.match(line)
        if m:
            # <tag>...
            self._init_multiline_tag(m.group(1))
            if m.group(2):
                self._parent().append_multiline_text(m.group(2))
        else:
            m = self._re_end_tags[-1].match(line)
            if m:
                # ...</tag>
                if m.group(1):
                    self._parent().append_multiline_text(m.group(1))
                self._end_multiline_tag()
            else:
                # only text, no tags
                self._parent().append_multiline_text(line)

    def opening_first_revision(self):
        return self._current_multiline_tag == "revision" and not self._opened_revision_arr

    def opening_another_revision(self):
        return self._current_multiline_tag == "revision" and self._opened_revision_arr

    def _init_multiline_tag(self, tag):
        self._current_multiline_tag = tag
        self._parent().add_tag(tag, self.opening_another_revision())
        self._parents.append(Node())
        self._add_re_end_tag(tag)
        if self.opening_first_revision():
            print("[")
            self._opened_revision_arr = True

    def _end_multiline_tag(self):
        self._previous_multiline_tag = self._current_multiline_tag
        self._current_multiline_tag = None
        self._parent().close(self._previous_multiline_tag)
        del self._parents[-1]
        del self._re_end_tags[-1]

    def _add_re_end_tag(self, tag):
        pattern = re.compile('(\s*\S.*)?\s*</%s>' % tag)
        self._re_end_tags.append(pattern)

    def _parent(self):
        return self._parents[-1]
