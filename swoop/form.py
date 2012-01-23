import urlparse
from collections import OrderedDict

from .request import Request
from .exceptions import ContentException

class PossibleValues(object):
    def __init__(self):
        self.values = {}

    def add(self, value, title=None):
        title = title or value
        self.values[title] = value


def add_radio(params, radio, values):
    name = radio.attrib['name']
    value = radio.attrib.get('value', '')
    checked = radio.attrib.get('checked', False)

    values.add(value)

    if name not in params and not checked:
        params[name] = None

    if checked:
        params[name] = value

def add_checkbox(params, checkbox, values):
    name = checkbox.attrib['name']
    value = checkbox.attrib.get('value', 'on')
    checked = checkbox.attrib.get('checked', False)

    values.add(value)
    params[name] = value if checked else None

def add_select(params, select, values):
    name = select.attrib['name']

    params[name] = None

    if select.attrib.get('multiple', False):
        first_value_set = True
    else:
        first_value_set = False

    for option in select.xpath('.//option'):
        if 'value' not in option.attrib:
            continue

        value = option.attrib['value']

        values.add(value)
        values.add(value, u'!#' + option.text)

        if not first_value_set or option.attrib.get('selected', False):
            first_value_set = True
            params[name] = value

def add_input(params, input):
    disabled = input.attrib.get('disabled', False)
    params[input.attrib['name']] = None if disabled else input.attrib.get('value', '')

def add_file(files, input):
    #disabled = input.attrib.get('disabled', False)
    files[input.attrib['name']] = ('', '')

def add_submit(params, input, values):
    name = input.attrib['name']
    params[name] = input.attrib['value']
    values.add(input.attrib['value'])

def get_request_for_form(response, action=None, id=None, idx=None, name=None, submit=True, values=None):
    forms = []
    for i, f in enumerate(response.xpath.many('//form')):
        if action and f.attrib['action'].endswith(action):
            forms.append(f)

        if id and f.attrib.get('id', None) == id:
            forms.append(f)

        if name and f.attrib.get('name', None) == name:
            forms.append(f)

        if idx is not None and i == idx:
            forms.append(f)

    if len(forms) > 1:
        raise ContentException('There are several forms for provided matchers: '
            'action=[%s] id=[%s] name=[%s]' % (str(action), str(id), str(name)))

    if not forms:
        raise ContentException('There are no any forms for provided mathers: '
            'action=[%s] id=[%s] name=[%s]' % (str(action), str(id), str(name)))

    form = forms[0]
    request = Request(
        urlparse.urljoin(response.url, form.attrib.get('action', response.url)),
        session_ref=response.session_ref)

    submit_already_added = submit is False
    params = OrderedDict()
    files = OrderedDict()

    possible_values = {}
    for input in form.xpath('.//*[self::input or self::select or self::textarea]'):
        input_name = input.attrib.get('name', None)
        if not input_name:
            continue

        if input.tag == 'input':
            input_type = input.attrib.get('type', 'text').lower()
        elif input.tag == 'select':
            input_type = 'select'
        elif input.tag == 'textarea':
            input_type = 'input'
        else:
            raise ContentException('Unknown widget %s' % input.tag)

        possible_value = possible_values.setdefault(input_name, PossibleValues())

        if input_type == 'radio':
            add_radio(params, input, possible_value)
        elif input_type == 'checkbox':
            add_checkbox(params, input, possible_value)
        elif input_type == 'select':
            add_select(params, input, possible_value)
        elif input_type == 'file':
            add_file(files, input)
        elif input_type in ('submit', 'image', 'button'):
            if not submit_already_added:
                if submit is True or input.attrib['name'] == submit:
                    add_submit(params, input, possible_value)
                    submit_already_added = True
        else:
            del possible_values[input_name]
            add_input(params, input)

    if values:
        for vname, value in values.items():
            if vname not in params:
                raise ContentException('There is no input [%s]. Existing: [%s]' % (
                    vname, '] ['.join(params.keys())))

            if value is None:
                params[vname] = None
            elif vname in possible_values:
                if value not in possible_values[vname].values:
                    raise ContentException(
                        'Input [%s] has no [%s] value. Existing: [%s]' % (vname, value,
                            '] ['.join(possible_values[vname].values.keys()) ))

                params[vname] = possible_values[vname].values[value]
            else:
                params[vname] = value

    request.files = files
    if form.attrib.get('method', 'GET').lower() == 'post':
        request.params = params
    else:
        request.query = params

    request.referer = response

    return request