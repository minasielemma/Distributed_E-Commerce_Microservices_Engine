from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, viewsets, mixins, permissions
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey, QuerySet
from rest_framework.decorators import action
from rest_framework.response import Response

def get_query_filter(model, field, base=""):
    try:
        model._meta.get_field(field)
        name = base + "__" + field if base else field
        return name
    except FieldDoesNotExist:
        value = None
        for item in model._meta.get_fields():
            if isinstance(item, ForeignKey):
                if model != item.related_model:
                    value = get_query_filter(
                        model=item.related_model,
                        field=field,
                        base=base + "__" + item.name if base else item.name,
                    )
                    if value:
                        return value
        return value

class BaseModelViewSet(viewsets.GenericViewSet):
    owner_field = "user"
    owner_queryset_filter_field = None

    def get_queryset(self):
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method." % self.__class__.__name__
        )

        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            if (
                self.owner_field is None
                or (
                    self.request.user.is_authenticated
                    and (
                        getattr(self.request.user, 'is_superuser', False)
                        or getattr(self.request.user, 'is_adminuser', False)
                    )
                )
            ):
                queryset = queryset.all()
            else:
                if not self.request.user.is_anonymous:
                    if self.owner_queryset_filter_field is None:
                        self.owner_queryset_filter_field = get_query_filter(
                            model=queryset.model, field=self.owner_field
                        )
                    if self.owner_queryset_filter_field:
                        all_entries = None
                        try:
                            all_entries = self.all_items
                        except AttributeError:
                            all_entries = None

                        if not all_entries:
                            queryset = self.queryset.filter(
                                **{self.owner_queryset_filter_field: self.request.user}
                            )
                    else:
                        queryset = self.queryset.none()
                else:
                    queryset = self.queryset.none()
        return queryset

class MultipleDeleteViewSet(viewsets.GenericViewSet):
    @extend_schema(
        request=inline_serializer(
            name='MultipleDeleteRequest',
            fields={'ids': serializers.ListField(child=serializers.IntegerField())}
        ),
        responses={
            200: inline_serializer(
                name='MultipleDeleteResponse',
                fields={'detail': serializers.CharField()}
            )
        }
    )
    @action(
        methods=["post"],
        detail=False,
        permission_classes=[permissions.IsAdminUser]
    )
    def multiple_delete(self, request):
        ids = request.data.get("ids")
        model = self.get_queryset().model
        model.objects.filter(id__in=ids).delete()

        return Response(
            {
                "detail": "Successfully deleted."
            },
            status=200,
        )

class ListViewSet(BaseModelViewSet, mixins.ListModelMixin):
    pass

class ListCreateViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
):
    pass

class ListCreateDeleteViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class ListCreateUpdateDeleteViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class ListRetrieveViewSet(
    BaseModelViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    pass

class ListRetrieveDeleteViewSet(
    BaseModelViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class ListDeleteViewSet(
    BaseModelViewSet,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class ListRetrieveUpdateViewSet(
    BaseModelViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
):
    pass

class ListRetrieveUpdateDeleteViewSet(
    BaseModelViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class ListCreateRetrieveDeleteViewSet(
    BaseModelViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class ListCreateRetrieveUpdateViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
):
    pass

class ListCreateUpdateViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
):
    pass

class ListCreateRetrieveViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    pass

class RetrieveDeleteViewSet(
    BaseModelViewSet,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class RetrieveUpdateViewSet(
    BaseModelViewSet,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
):
    pass

class RetrieveUpdateDeleteViewSet(
    BaseModelViewSet,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class CreateRetrieveViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
):
    pass

class CreateRetrieveUpdateViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
):
    pass

class CreateRetrieveUpdateDeleteViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class CreateRetrieveDeleteViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class CreateDeleteViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class CreateUpdateDeleteViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class FullBaseViewSet(
    BaseModelViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    pass

class DeleteViewSet(
    BaseModelViewSet,
    mixins.DestroyModelMixin,
):
    pass
