from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.urls import reverse
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from .models import Bestallare

from django.core import mail
from django.core.mail import EmailMultiAlternatives, get_connection, message, send_mail

import codecs
import io
import xlsxwriter

import datetime

from .forms import ChooseExportAttributes

import logging
from pdb import set_trace

logger = logging.getLogger(__name__)

predetermined_column_order =  ['official_id',
                               'term',
                               'synonym',
                               'definition',
                               'källa',
                               'anmärkningar',
                               'status',
                               'beställare',
                               'begrepp_kontext',
                               'kommentar_handläggning',
                               'utländsk_term',
                               'annan_ordlista',
                               'externt_id',
                               'senaste_ändring',
                               'begrepp_version_nummer',
                               'datum_skapat',
                               'term_i_system',
                               'tidigare_definition_och_källa',
                               'id']

def get_synonym_set(obj):
    
    query = getattr(obj, 'synonym_set')
    return_list = []
    for synonym in query.values_list('synonym','synonym_status'):
        return_list.append(f'{synonym[0]} - {synonym[1]}')
    if len(return_list) > 0:
        return ', '.join(return_list)
    else:
        return ''

def export_chosen_begrepp_as_csv(request, queryset, field_names='all'):

    
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True})
    date_format = workbook.add_format({'num_format': 'YYYY-MM-DD H:M:S'})

    chosen_columns = [i for i in predetermined_column_order if i in field_names]
    zipped_list = zip(chosen_columns, field_names)
    field_names = [x[0] for x in zipped_list]
    logger.debug(f"column order of export file --> {field_names}")
    row_index=0
    col_index=0
    worksheet.write_row(row_index,col_index,field_names, bold)
    length=40

    for obj in queryset:
        row_index += 1
        worksheet.set_row(row_index, 15)
        for col_index, field in enumerate(field_names):
            worksheet.set_column(row_index, col_index, length)
            if field == 'synonym':
                field_value = get_synonym_set(obj)
                worksheet.write(row_index, col_index, field_value)
                logger.debug(f'writing {field} - {field_value}')
            elif field == 'term':
                field_value = getattr(obj, field)
                link = request.build_absolute_uri(reverse('begrepp_förklaring'))  + f'?q={obj.pk}'
                worksheet.write_url(row=row_index, col=col_index, url=link, string=field_value)
                logger.debug(f'writing {field} - {field_value}')
            elif field == 'beställare':
                field_value = getattr(obj, field).beställare_namn
                worksheet.write(row_index, col_index, field_value)
                logger.debug(f'writing {field} - {field_value}')
            elif field in ['datum_skapat', 'begrepp_version_nummer']:
                field_value = getattr(obj, field)
                worksheet.write(row_index, col_index, field_value, date_format)
            else:
                field_value = getattr(obj, field)
                if (type(field_value) == str) and (len(field_value) > 80):
                    worksheet.set_column(col_index, col_index, length)
                    worksheet.write(row_index, col_index, field_value)
                else:
                    worksheet.write(row_index, col_index, field_value)
                logger.debug(f'writing {field} - {field_value}')
    workbook.close()
    output.seek(0)

    filename = f"{queryset.first()._meta.object_name.lower()}_export_{datetime.datetime.now().strftime('%Y_%m_%d-%H:%M:%S')}.xlsx"
    logger.debug(f"field_names for ACTION begrepp_export - {field_names}")
    response = HttpResponse(
        output, 
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response