from django.db.models import Q

class GeneralFilter:
    @staticmethod
    def apply_filters(queryset, request, search_fields=None, default_ordering='-id'):
        if search_fields and 'search' in request.query_params:
            search_query = request.query_params.get('search', '').strip()
            if search_query:
                q_objects = Q()
                for field in search_fields:
                    q_objects |= Q(**{f"{field}__icontains": search_query})
                queryset = queryset.filter(q_objects)

        ordering = request.query_params.get('ordering', default_ordering)
        if ordering:
            try:
                queryset = queryset.order_by(*ordering.split(','))
            except Exception:
                queryset = queryset.order_by(default_ordering)

        return queryset
