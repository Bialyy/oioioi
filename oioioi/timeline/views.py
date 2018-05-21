import datetime
from collections import defaultdict
from operator import itemgetter  # pylint: disable=E0611

import six
from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.urlresolvers import reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from oioioi.base.permissions import enforce_condition
from oioioi.contests.date_registration import date_registry
from oioioi.contests.menu import contest_admin_menu_registry
from oioioi.contests.models import Round
from oioioi.contests.utils import contest_exists, is_contest_admin


def _get_date_id(registry_item):
    date_id = six.text_type(registry_item['model']._meta.verbose_name) + ":" + \
            str(registry_item['id']) + ":" + \
            six.text_type(registry_item['date_field'])
    return date_id.replace(' ', '_')


def _make_group_registry(registry):
    group_registry = defaultdict(list)
    for item in registry:
        item['type'] = None
        if item['model'] == Round:
            if item['date_field'] == 'start_date':
                item['type'] = 'start'
            elif item['date_field'] == 'end_date':
                item['type'] = 'end'
        round_id = getattr(item['round'], 'id', 0)
        round_name = getattr(item['round'], 'name', '')
        group_registry[round_id, round_name].append(item)
    return sorted(six.iteritems(group_registry), key=itemgetter(0))


def _translate_field(field, obj):
    if field == NON_FIELD_ERRORS:
        return None
    return obj._meta.get_field_by_name(field)[0].verbose_name


@contest_admin_menu_registry.register_decorator(_("Timeline"), lambda request:
        reverse('timeline_view', kwargs={'contest_id': request.contest.id}))
@enforce_condition(contest_exists & is_contest_admin)
def timeline_view(request):
    registry = date_registry.tolist(request.contest.id)
    group_registry = _make_group_registry(registry)

    for item in registry:
        item['date_id'] = _get_date_id(item)

    if request.POST:
        tosave = {}
        error_list = []
        for item in registry:
            date = request.POST.get(item['date_id'], None)
            obj = item['model'].objects.get(pk=item['id'])
            if date:
                try:
                    current_tz = timezone.get_current_timezone()
                    parsed_date = current_tz.localize(
                            datetime.datetime.strptime(date, "%Y-%m-%d %H:%M"))
                except ValueError:
                    error_list.append((six.text_type(item['text']),
                            {None: [_("Date format is invalid")]}))
                    continue
            else:
                if not getattr(obj, item['date_field']):
                    continue
                parsed_date = None

            item['date'] = parsed_date
            obj_str = six.text_type(item['model']) + str(item['id'])
            if obj_str in tosave:
                setattr(tosave[obj_str], item['date_field'], parsed_date)
            else:

                setattr(obj, item['date_field'], parsed_date)
                tosave[obj_str] = obj

        for obj in tosave.values():
            try:
                obj.full_clean()
            except ValidationError as e:
                object_name = getattr(obj, 'name', None)
                if not object_name:
                    object_name = '%s (%s)' % (obj._meta.verbose_name.title(),
                            obj.id)
                message_dict = dict((_translate_field(field, obj), value)
                        for (field, value) in e.message_dict.items())
                error_list.append((object_name, message_dict))

        if error_list:
            return TemplateResponse(request, 'timeline/timeline_view.html',
                    {'registry': group_registry,
                    'error_list': sorted(error_list),
                    'server_timezone': settings.TIME_ZONE})

        for obj in tosave.values():
            obj.save()

    return TemplateResponse(request, 'timeline/timeline_view.html',
                {'registry': group_registry,
                 'server_timezone': settings.TIME_ZONE})
