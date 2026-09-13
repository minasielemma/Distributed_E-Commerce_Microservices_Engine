from django.db.models import Q

class GeneralFilter:
    @staticmethod
    def apply_filters(queryset, request, search_fields=None, filter_map=None, default_ordering='-created_at'):
        params = request.query_params

        search_query = params.get('search')
        if search_query and search_fields:
            q_objects = Q()
            for field in search_fields:
                q_objects |= Q(**{f"{field}__icontains": search_query})
            queryset = queryset.filter(q_objects)

        # Check tenant / shop filtering across query params and HTTP headers
        parser_ctx = getattr(request, 'parser_context', {}) or {}
        is_detail_lookup = bool(parser_ctx and parser_ctx.get('kwargs', {}).get('pk'))

        query_tenant_id = (
            params.get('tenant_id') or
            params.get('shop_id') or
            params.get('shop') or
            params.get('tenant')
        )

        header_tenant_id = (
            (request.headers.get('X-Tenant-Id') if hasattr(request, 'headers') else None) or
            (request.headers.get('X-Tenant-ID') if hasattr(request, 'headers') else None) or
            (request.META.get('HTTP_X_TENANT_ID') if hasattr(request, 'META') else None) or
            (request.META.get('HTTP_X_TENANT_Id') if hasattr(request, 'META') else None)
        )

        tenant_id = query_tenant_id or (None if is_detail_lookup else header_tenant_id)

        if tenant_id and tenant_id != '':
            has_tenant_field = any(f.name == 'tenant_id' for f in queryset.model._meta.get_fields())
            if has_tenant_field:
                queryset = queryset.filter(Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))

        if filter_map:
            for param_key, db_field in filter_map.items():
                val = params.get(param_key)
                if val is not None and val != '':
                    queryset = queryset.filter(**{db_field: val})

        min_price = params.get('min_price')
        if min_price:
            if hasattr(queryset.model, 'price_detail'):
                queryset = queryset.filter(price_detail__base_price__gte=min_price)

        max_price = params.get('max_price')
        if max_price:
            if hasattr(queryset.model, 'price_detail'):
                queryset = queryset.filter(price_detail__base_price__lte=max_price)

        is_available = params.get('is_available')
        if is_available is not None and is_available != '':
            if is_available.lower() in ['true', '1']:
                # Only apply status filter if the model actually has a DB status column
                status_field = queryset.model._meta.get_field('status') if any(
                    f.name == 'status' for f in queryset.model._meta.get_fields()
                ) else None
                if status_field:
                    queryset = queryset.filter(status='ACTIVE')

        start_date = params.get('start_date')
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        end_date = params.get('end_date')
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        ordering = params.get('ordering')
        if ordering:
            if ordering == 'price_asc' and hasattr(queryset.model, 'price_detail'):
                queryset = queryset.order_by('price_detail__base_price')
            elif ordering == 'price_desc' and hasattr(queryset.model, 'price_detail'):
                queryset = queryset.order_by('-price_detail__base_price')
            elif ordering == 'name_asc':
                queryset = queryset.order_by('name')
            elif ordering == 'name_desc':
                queryset = queryset.order_by('-name')
            else:
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
