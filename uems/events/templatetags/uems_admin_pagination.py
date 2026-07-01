from django import template
from django.contrib.admin.views.main import ALL_VAR, PAGE_VAR


register = template.Library()


@register.simple_tag
def uems_admin_pagination(cl):
    current_page = cl.page_num
    num_pages = max(cl.paginator.num_pages, 1)
    count = cl.result_count

    def page_url(page_number):
        return cl.get_query_string({PAGE_VAR: page_number})

    page_items = []

    for page_number in cl.paginator.get_elided_page_range(current_page):
        is_ellipsis = page_number == cl.paginator.ELLIPSIS
        page_items.append({
            "label": page_number,
            "url": "" if is_ellipsis else page_url(page_number),
            "current": page_number == current_page,
            "ellipsis": is_ellipsis,
        })

    if not page_items:
        page_items.append({
            "label": 1,
            "url": page_url(1),
            "current": True,
            "ellipsis": False,
        })

    return {
        "count": count,
        "start": count and ((current_page - 1) * cl.list_per_page) + 1,
        "end": min(current_page * cl.list_per_page, count),
        "has_previous": current_page > 1,
        "previous_url": page_url(current_page - 1),
        "has_next": current_page < num_pages,
        "next_url": page_url(current_page + 1),
        "page_items": page_items,
        "verbose_name": cl.opts.verbose_name,
        "verbose_name_plural": cl.opts.verbose_name_plural,
        "show_all_url": cl.get_query_string({ALL_VAR: ""}) if cl.can_show_all and not cl.show_all and cl.multi_page else "",
    }
