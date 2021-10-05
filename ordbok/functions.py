from pdb import set_trace
from .models import SökData, SökFörklaring, Bestallare

from collections import OrderedDict

import re
import datetime

def besökare_ip_adress(request):

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def mäta_sök_träff(sök_term, sök_data, request):

    ny_sök = SökData()
    ny_sök.sök_term = sök_term
    ny_sök.records_returned = str([i.get('begrepp_id') for i in sök_data])[1:-1]
    ny_sök.ip_adress = besökare_ip_adress(request)
    ny_sök.save()
    return None

def mäta_förklaring_träff(sök_term, request):

    ny_sök = SökFörklaring()
    ny_sök.sök_term = sök_term
    ny_sök.ip_adress = besökare_ip_adress(request)
    ny_sök.save()

def sort_begrepp_keys(begrepp_dict):

    desired_dict_order = ['status',
                          'term',
                          'synonym',
                          'definition',
                          'källa',
                          'anmärkning',
                          'term på annat språk',
                          'annan referens',
                          'kod',
                          'term id']
    
    return OrderedDict([(v, begrepp_dict[v]) for v in desired_dict_order])

def nbsp2space(string_with_bad_values):
    
    '''
    Replace a nonbreaking space (nbs) (Latin) with a normal space. The nbs can cause problems
    in html rendering.

    '''
    return re.sub('\\xa0', ' ', string_with_bad_values, flags=re.IGNORECASE|re.UNICODE)

class Xlator(dict):
    """ All-in-one multiple-string-substitution class
        a version to substitute only entire words """

    def escape_keys(self):
        
        return [re.escape(i) for i in self.keys()]

    def _make_regex(self):
        
        escaped_keys = self.escape_keys()
        joined_keys = r'\b'+r'\b|\b'.join(escaped_keys)
        compiled_re = re.compile(joined_keys+r'\b')
        
        return compiled_re

    def __call__(self, match):
        """ Handler invoked for each regex match """
        return self[match.group(0)]

    def xlat(self, text):
        """ Translate text, returns the modified text. """
        return self._make_regex().sub(self, text)


HTML_TAGS = ['a', 'abbr', 'acronym', 'address', 'applet', 'area', 'article', 'aside',
'audio', 'b', 'base', 'basefont', 'bb', 'bdo', 'big', 'blockquote', 'body', 'br /', 'br',
'button', 'canvas', 'caption', 'center', 'cite', 'code', 'col', 'colgroup', 'command',
'datagrid', 'datalist', 'dd', 'del', 'details', 'dfn', 'dialog', 'dir', 'div', 'dl', 
'dt', 'em', 'embed', 'eventsource', 'fieldset', 'figcaption', 'figure', 'font', 'footer', 
'form', 'frame', 'frameset', 'h1 to h6', 'head', 'header', 'hgroup', 'hr /', 'html',
'i', 'iframe', 'img', 'input', 'ins', 'isindex', 'kbd', 'keygen', 'label', 'legend',
'li', 'link', 'map', 'mark', 'menu', 'meta', 'meter', 'nav', 'noframes', 'noscript',
'object', 'ol', 'optgroup', 'option', 'output', 'p', 'param', 'pre', 'progress', 'q',
'rp', 'rt', 'ruby', 's', 'samp', 'script', 'section', 'select', 'small', 'source',
'span', 'strike', 'strong', 'style', 'sub', 'sup', 'table', 'tbody', 'td', 'textarea',
'tfoot', 'th', 'thead', 'time', 'title', 'tr', 'track', 'tt', 'u', 'ul', 'var',
'video', 'wbr']