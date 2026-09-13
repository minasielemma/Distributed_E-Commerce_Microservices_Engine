from django.db.models import Q

class GeneralFilter:
    @staticmethod
    def apply_filters(queryset, request, search_fields=None, filter_map=None, default_ordering='-updated_at'):
        if not queryset.exists():
            return queryset

        params = request.query_params

        search_query = params.get('search')
        if search_query and search_fields:
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(q_objects)

        if filter_map:
            for param_key, db_field in filter_map.items():
                val = params.get(param_key)
                if val is not None and val != '':
                    queryset = queryset.filter(**{db_field: val})

        ordering = params.get('ordering')
        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                pass
        elif default_ordering:
            try:
                queryset = queryset.order_by(default_ordering)
            except Exception:
                pass

        return queryset
