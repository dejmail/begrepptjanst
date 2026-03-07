import datetime
import io
import logging
from typing import Any, Dict, List

import xlsxwriter
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import get_deleted_objects
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse

from term_list.models import Attribute, Dictionary

logger = logging.getLogger(__name__)

predetermined_column_order =  ['id_vgr',
                               'term',
                               'synonym',
                               'definition',
                               'källa',
                               'anmärkningar',
                               'status',
                               'beställare',
                               'begrepp_kontext',
                               'kommentar_handläggning',
                               'non_swedish_terrm',
                               'annan_ordlista',
                               'externt_id',
                               'senaste_ändring',
                               'begrepp_version_nummer',
                               'datum_skapat',
                               'term_i_system',
                               'tidigare_definition_och_källa',
                               'id']

def get_synonym_set(obj):

    query = getattr(obj, 'synonyms')
    return_list = []
    for synonym in query.values_list('synonym','synonym_status'):
        return_list.append(f'{synonym[0]} - {synonym[1]}')
    if len(return_list) > 0:
        return ', '.join(return_list)
    else:
        return ''

def export_chosen_concept_as_csv(request: HttpRequest,
                                 queryset : QuerySet,
                                 selected_fields : List[str],
                                 field_mapping: Dict[str, Any]):

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    date_format = workbook.add_format({'num_format': 'YYYY-MM-DD HH:MM:SS'})

    # Formatting
    bold = workbook.add_format({'bold': True})

    # Write Header Row
    worksheet.write_row(0, 0, selected_fields, bold)

    # Write Data Rows
    for row_idx, obj in enumerate(queryset, start=1):
        for col_index, field in enumerate(selected_fields):
            if field.lower() == 'synonyms':
                row_data = get_synonym_set(obj)
                worksheet.write(row_idx, col_index, row_data)
            elif field.lower() == 'term':
                row_data = getattr(obj, field.lower(), "")
                link = request.build_absolute_uri(reverse('term_metadata'))  + f'?q={obj.pk}'
                worksheet.write_url(row=row_idx, col=col_index, url=link, string=row_data)
            elif (field in field_mapping.keys()) and (field in ['Senaste ändring', 'Datum skapat']):
                logger.debug('Found date, fixing format')
                field_name = field_mapping.get(field, '')
                row_data = getattr(obj, str(field_name), None)
                worksheet.write(row_idx, col_index, row_data, date_format)
            elif field.lower() == 'dictionaries':
                row_data = ', '.join([dictionary.dictionary_name for dictionary in obj.dictionaries.all()])
                worksheet.write(row_idx, col_index, row_data)
            else:
                if hasattr(obj, field.lower()):
                    row_data = getattr(obj, field.lower(), "")
                else:
                    matching_attr = next((attr for attr in obj.attributes.all() if attr.attribute.display_name == field), None)
                    row_data = matching_attr.get_value() if matching_attr else ""

                worksheet.write(row_idx, col_index, row_data)

    workbook.close()
    output.seek(0)

    # Prepare Response
    response = HttpResponse(output, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="exporterad_begrepp_{datetime.datetime.now().strftime("%Y_%m_%d-%H:%M:%S")}.xlsx"'

    return response

def delete_allowed_objects(
    modeladmin, request, queryset, *,
    object_label="objekt",
    permission_check=None
):
    opts = modeladmin.model._meta
    app_label = opts.app_label

    # Use provided permission checker or fallback to modeladmin
    if permission_check is None:
        permission_check = modeladmin._user_has_dictionary_access

    deletable = [obj for obj in queryset if permission_check(request, obj)]

    if not deletable:
        modeladmin.message_user(
            request,
            f"Inga av de valda {object_label} kan raderas baserat på dina gruppbehörigheter.",
            level=messages.WARNING,
        )
        return

    if request.POST.get("post"):
        try:
            with transaction.atomic():
                count = len(deletable)
                for obj in deletable:
                    obj.delete()
                modeladmin.message_user(
                    request,
                    f"Raderade {count} {object_label}.",
                    level=messages.SUCCESS,
                )
        except Exception as e:
            modeladmin.message_user(
                request,
                f"Ett fel uppstod under radering: {str(e)}",
                level=messages.ERROR,
            )
        return redirect(request.get_full_path())

    deletable_objects, model_count, perms_needed, protected = get_deleted_objects(
        objs=deletable,
        request=request,
        admin_site=modeladmin.admin_site,
    )

    if perms_needed:
        raise PermissionDenied(
            f"Du har inte tillräckliga rättigheter för att radera dessa {object_label}."
        )

    context = {
        **modeladmin.admin_site.each_context(request),
        "title": "Är du säker?",
        "objects_name": str(opts.verbose_name_plural),
        "deletable_objects": deletable_objects,
        "queryset": deletable,
        "action": request.POST.get("action"),
        "opts": opts,
        "app_label": app_label,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
    }

    return TemplateResponse(
        request,
        "admin/delete_selected_intermediate.html",
        context,
    )


def change_dictionaries(modeladmin, request, queryset):
    logger = logging.getLogger(__name__)

    logger.info("change_dictionaries action called.")

    if 'apply' in request.POST:
        selected_dictionaries = request.POST.getlist('dictionaries')
        if selected_dictionaries:
            dictionaries = Dictionary.objects.filter(pk__in=selected_dictionaries)
            for begrepp in queryset:
                begrepp.dictionaries.set(dictionaries)
            modeladmin.message_user(request, f"{queryset.count()} Begrepp updated with the selected Dictionaries.")
        return redirect(request.get_full_path())

    # Prepare context including _selected_action and select_across
    context = {
        'queryset': queryset,
        'dictionaries': Dictionary.objects.all(),
        'action_name': 'change_dictionaries',
        'selected_action': request.POST.getlist('_selected_action'),
        'select_across': request.POST.get('select_across'),
    }
    return render(request, 'admin/change_dictionary_action.html', context)

change_dictionaries.short_description = "Change Dictionaries of selected Begrepp"  # type: ignore[attr-defined]


def export_chosen_concepts_action(modeladmin, request, queryset):

    db_table_attrs = [
    field.verbose_name.capitalize() if hasattr(field, "verbose_name") and field.verbose_name else field.name.capitalize()
    for field in queryset.first()._meta.get_fields()
    if field.name not in ['concept_fk', 'conceptcomment', 'conceptexternalfiles', 'attributes']
    ]

    attribute_names = Attribute.objects.filter(
        attributevalue__term__in=queryset
    ).values_list('display_name', flat=True).distinct()

    db_table_attrs.extend(attribute_names)
    chosen_concepts = [{'pk': i[0], 'term': i[1]} for i in queryset.values_list('pk', 'term')]

    return render(request, "choose_export_attrs_intermediate.html", context={"db_table_attrs" : db_table_attrs,
                                                                            "chosen_concepts" : chosen_concepts})

export_chosen_concepts_action.short_description = "Exportera valde begrepp"  # type: ignore[attr-defined]

def ändra_status_till_översättning(queryset):

    queryset.update(status='Översättning')
