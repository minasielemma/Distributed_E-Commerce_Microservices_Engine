import uuid 
import logging 
from decimal import Decimal 
from django.db import transaction 
from django.db.models import Q, Count 
from rest_framework import viewsets, permissions, status 
from rest_framework .response import Response 
from rest_framework .decorators import action 
from common.viewsets import FullBaseViewSet 
from common.filters import GeneralFilter 
from common.audit_logger import log_audit_event 
from common.permissions import IsStoreOwnerOrPlatformAdmin, IsTenantMember, _is_platform_admin 
from .models import (
Category ,Product ,ProductLike ,PriceDiscount ,
ProductAttribute ,ProductAttributeValue ,ProductVariant ,
ProductImage ,ProductReview ,DiscountCode ,CouponRedemption 
)
from .serializers import (
CategorySerializer ,ProductSerializer ,ProductLikeSerializer ,PriceDiscountSerializer ,
ProductAttributeSerializer ,ProductAttributeValueSerializer ,ProductVariantSerializer ,
ProductImageSerializer ,ProductReviewSerializer ,DiscountCodeSerializer 
)

logger =logging .getLogger (__name__ )

class CategoryViewSet(FullBaseViewSet):
    permission_classes = (IsStoreOwnerOrPlatformAdmin,)
    serializer_class = CategorySerializer
    queryset = Category.objects.prefetch_related('subcategories').all()

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        qs = Category.objects.prefetch_related('subcategories').all()
        user = getattr(self.request, 'user', None)

        if not _is_platform_admin(user):
            user_tenant = getattr(user, 'tenant_id', None) if (user and user.is_authenticated) else None
            if user_tenant:
                qs = qs.filter(Q(tenant_id=user_tenant) | Q(is_global=True) | Q(tenant_id__isnull=True))
            else:
                qs = qs.filter(Q(is_global=True) | Q(tenant_id__isnull=True))

        is_main = self.request.query_params.get('is_main')
        parent_id = self.request.query_params.get('parent')
        fetch_all = self.request.query_params.get('all') or self.request.query_params.get('fetch_all')
        search_term = self.request.query_params.get('search')

        if search_term:
            if parent_id:
                qs = qs.filter(parent_id=parent_id)
        elif is_main is not None:
            qs = qs.filter(parent__isnull=True) if is_main.lower() == 'true' else qs.filter(parent__isnull=False)
        elif parent_id:
            qs = qs.filter(parent_id=parent_id)
        elif not (fetch_all and fetch_all.lower() == 'true') and not self.kwargs.get('pk') and self.action not in ('retrieve', 'update', 'partial_update', 'destroy'):
            qs = qs.filter(parent__isnull=True)

        limit = self.request.query_params.get('limit')
        if limit and limit.isdigit():
            qs = qs[:int(limit)]

        return GeneralFilter.apply_filters(qs, self.request, search_fields=['name', 'slug'], default_ordering='name')

    def paginate_queryset(self, queryset):
        fetch_all = (
            self.request.query_params.get('all')
            or self.request.query_params.get('fetch_all')
            or self.request.query_params.get('no_page')
        )
        limit = self.request.query_params.get('limit')
        if limit and limit.isdigit():
            return None
        if fetch_all and str(fetch_all).lower() == 'true':
            return None
        return super().paginate_queryset(queryset)

    def perform_create(self, serializer):
        user = self.request.user
        if _is_platform_admin(user):
            is_global = serializer.validated_data.get('is_global', True)
            tenant_id = serializer.validated_data.get('tenant_id')
            serializer.save(tenant_id=tenant_id, is_global=is_global)
        else:
            tenant_id = getattr(user, 'tenant_id', None)
            serializer.save(tenant_id=tenant_id, is_global=False)

    def perform_update(self, serializer):
        instance = serializer.instance
        user = self.request.user
        if not _is_platform_admin(user):
            if instance.is_global or instance.tenant_id is None or str(instance.tenant_id) != str(getattr(user, 'tenant_id', '')):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Store owners cannot modify global or competitor categories.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if not _is_platform_admin(user):
            if instance.is_global or instance.tenant_id is None or str(instance.tenant_id) != str(getattr(user, 'tenant_id', '')):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Store owners cannot delete global or competitor categories.")
        instance.delete()

class PriceDiscountViewSet(FullBaseViewSet):
    # Only the owning tenant can read or write their discounts
    permission_classes = (IsTenantMember,)
    serializer_class = PriceDiscountSerializer
    queryset = PriceDiscount.objects.select_related('product', 'category').all()

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        qs = PriceDiscount.objects.select_related('product', 'category')
        if not _is_platform_admin(self.request.user):
            tenant_id = getattr(self.request.user, 'tenant_id', None)
            if tenant_id:
                qs = qs.filter(tenant_id=tenant_id)
            else:
                qs = qs.none()
        return GeneralFilter.apply_filters(qs, self.request, search_fields=['title'], default_ordering='-start_time')

    def perform_create(self, serializer):
        serializer.save(tenant_id=getattr(self.request.user, 'tenant_id', None))

class ProductAttributeViewSet(FullBaseViewSet):
    permission_classes = (IsTenantMember,)
    serializer_class = ProductAttributeSerializer
    queryset = ProductAttribute.objects.prefetch_related('values').all()

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        qs = ProductAttribute.objects.prefetch_related('values')
        if not _is_platform_admin(self.request.user):
            tenant_id = getattr(self.request.user, 'tenant_id', None)
            from django.db.models import Q
            if tenant_id:
                qs = qs.filter(Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))
            else:
                qs = qs.filter(tenant_id__isnull=True)
        return GeneralFilter.apply_filters(qs, self.request, search_fields=['name', 'category'], default_ordering='display_order')

    def paginate_queryset(self, queryset):
        fetch_all = (
            self.request.query_params.get('all')
            or self.request.query_params.get('fetch_all')
            or self.request.query_params.get('no_page')
        )
        if fetch_all and str(fetch_all).lower() == 'true':
            return None
        return super().paginate_queryset(queryset)

    def perform_create(self, serializer):
        serializer.save(tenant_id=getattr(self.request.user, 'tenant_id', None))


class ProductAttributeValueViewSet(FullBaseViewSet):
    permission_classes = (IsTenantMember,)
    serializer_class = ProductAttributeValueSerializer
    queryset = ProductAttributeValue.objects.select_related('attribute').all()

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        qs = ProductAttributeValue.objects.select_related('attribute')
        if not _is_platform_admin(self.request.user):
            tenant_id = getattr(self.request.user, 'tenant_id', None)
            from django.db.models import Q
            if tenant_id:
                qs = qs.filter(Q(attribute__tenant_id=tenant_id) | Q(attribute__tenant_id__isnull=True))
            else:
                qs = qs.filter(attribute__tenant_id__isnull=True)
        return qs


class ProductVariantViewSet(FullBaseViewSet):
    permission_classes = (IsTenantMember,)
    serializer_class = ProductVariantSerializer
    queryset = ProductVariant.objects.select_related('product').prefetch_related('attribute_values__attribute').all()

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        qs = ProductVariant.objects.select_related('product').prefetch_related('attribute_values__attribute')
        product_id = self.request.query_params.get('product_id')
        if product_id:
            qs = qs.filter(product_id=product_id)
        elif self.request.method not in permissions.SAFE_METHODS:
            if not _is_platform_admin(self.request.user):
                tenant_id = getattr(self.request.user, 'tenant_id', None)
                if tenant_id:
                    qs = qs.filter(product__tenant_id=tenant_id)
                else:
                    qs = qs.none()
        return GeneralFilter.apply_filters(qs, self.request, search_fields=['sku'],
            filter_map={'product_id': 'product_id', 'sku': 'sku'}, default_ordering='-created_at')

    def perform_create(self, serializer):
        serializer.save(tenant_id=getattr(self.request.user, 'tenant_id', None))


class ProductImageViewSet(FullBaseViewSet):
    permission_classes = (IsTenantMember,)
    serializer_class = ProductImageSerializer
    queryset = ProductImage.objects.select_related('product', 'variant').all()

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        qs = ProductImage.objects.select_related('product', 'variant')
        product_id = self.request.query_params.get('product_id')
        if product_id:
            qs = qs.filter(product_id=product_id)
        elif self.request.method not in permissions.SAFE_METHODS:
            if not _is_platform_admin(self.request.user):
                tenant_id = getattr(self.request.user, 'tenant_id', None)
                if tenant_id:
                    qs = qs.filter(product__tenant_id=tenant_id)
                else:
                    qs = qs.none()
        return GeneralFilter.apply_filters(qs, self.request, search_fields=['alt_text'],
            filter_map={'product_id': 'product_id', 'variant_id': 'variant_id'}, default_ordering='display_order')

    def perform_create(self, serializer):
        serializer.save(tenant_id=getattr(self.request.user, 'tenant_id', None))

class ProductReviewViewSet (FullBaseViewSet ):
    permission_classes =(permissions .AllowAny ,)
    serializer_class =ProductReviewSerializer 
    queryset =ProductReview .objects .select_related ('product').all ()

    def get_queryset (self ):
        qs =ProductReview .objects .select_related ('product').all ()
        filter_map ={
        'product_id':'product_id',
        'user_id':'user_id',
        }
        return GeneralFilter .apply_filters (qs ,self .request ,search_fields =['title','review_text'],filter_map =filter_map ,default_ordering ='-created_at')

    def perform_create (self ,serializer ):
        tenant_id =getattr (self .request .user ,'tenant_id',None )
        user_id =self .request .user .id if self .request .user .is_authenticated else None 
        user_name = getattr(self.request.user, 'username', '') if (self.request.user and self.request.user.is_authenticated) else 'Anonymous'
        if not user_name:
            user_name = 'Anonymous'
        review = serializer .save (tenant_id =tenant_id ,user_id =user_id ,user_name =user_name )
        if user_id and getattr(review, 'product_id', None):
            try:
                import json, uuid
                try:
                    from kafka import KafkaProducer
                except ImportError:
                    from kafka_ng import KafkaProducer
                producer = KafkaProducer(
                    bootstrap_servers='kafka:9092',
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                producer.send('ecommerce-events', value={
                    'event_id': str(uuid.uuid4()),
                    'event_type': 'review.created',
                    'payload': {
                        'user_id': str(user_id),
                        'product_id': str(review.product_id),
                        'tenant_id': str(tenant_id) if tenant_id else None,
                        'rating': getattr(review, 'rating', 5)
                    }
                })
                producer.flush()
            except Exception as e:
                logger.warning(f"Failed publishing review.created to Kafka: {e}")

class DiscountCodeViewSet(FullBaseViewSet):
    permission_classes = (IsTenantMember,)
    serializer_class = DiscountCodeSerializer
    queryset = DiscountCode.objects.all()

    def get_queryset(self):
        qs = DiscountCode.objects.all()
        if not _is_platform_admin(self.request.user):
            tenant_id = getattr(self.request.user, 'tenant_id', None)
            if tenant_id:
                qs = qs.filter(tenant_id=tenant_id)
            else:
                qs = qs.none()
        return GeneralFilter.apply_filters(qs, self.request, search_fields=['code'], default_ordering='-created_at')

    def perform_create(self, serializer):
        serializer.save(tenant_id=getattr(self.request.user, 'tenant_id', None))


    @action (detail =False ,methods =['post'],url_path ='validate', permission_classes=[permissions.AllowAny])
    def validate_code (self ,request ):
        """Stateless check — does NOT increment usage.  Use /redeem/ to reserve."""
        code_str =request .data .get ('code','').strip ().upper ()
        subtotal_raw =request .data .get ('subtotal')or request .data .get ('order_subtotal','0.00')
        customer_id =getattr (request .user ,'id',None )if request .user .is_authenticated else None 
        try :
            subtotal =Decimal (str (subtotal_raw ))
        except Exception :
            return Response ({'valid':False ,'message':'Invalid subtotal format.'},status =status .HTTP_400_BAD_REQUEST )

        if not code_str :
            return Response ({'valid':False ,'message':'Coupon code is required.'},status =status .HTTP_400_BAD_REQUEST )

        try :
            coupon =DiscountCode .objects .get (code__iexact =code_str )
        except DiscountCode .DoesNotExist :
            return Response ({'valid':False ,'message':'Invalid coupon code.'},status =status .HTTP_404_NOT_FOUND )

        is_valid ,msg =coupon .is_valid (subtotal =subtotal ,customer_id =customer_id )
        if not is_valid :
            return Response ({'valid':False ,'message':msg },status =status .HTTP_400_BAD_REQUEST )

        discount_amount =coupon .calculate_discount (subtotal )
        return Response ({
        'valid':True ,
        'code':coupon .code ,
        'discount_type':coupon .discount_type ,
        'value':str (coupon .value ),
        'discount_amount':str (discount_amount ),
        'message':'Coupon code applied successfully.'
        },status =status .HTTP_200_OK )


    @action (detail =False ,methods =['post'],url_path ='redeem',
    permission_classes =[permissions .IsAuthenticated ])
    def redeem (self ,request ):
        """Atomically reserve a coupon for an order.

        Expected body:
            { "code": "PROMO10", "order_id": "<uuid>",
              "subtotal": "150.00" }

        Returns the CouponRedemption record on success (status PENDING).
        Idempotent: calling again with the same order_id returns the existing
        reservation if it is still PENDING.
        """
        code_str =request .data .get ('code','').strip ().upper ()
        order_id_str =request .data .get ('order_id','').strip ()
        subtotal_raw =request .data .get ('subtotal','0.00')
        customer_id =request .user .id 

        if not code_str :
            return Response ({'error':'Coupon code is required.'},status =status .HTTP_400_BAD_REQUEST )
        try :
            order_id =uuid .UUID (order_id_str )
        except (ValueError ,AttributeError ):
            return Response ({'error':'Valid order_id (UUID) is required.'},status =status .HTTP_400_BAD_REQUEST )
        try :
            subtotal =Decimal (str (subtotal_raw ))
        except Exception :
            return Response ({'error':'Invalid subtotal format.'},status =status .HTTP_400_BAD_REQUEST )


        existing =CouponRedemption .objects .filter (
        order_id =order_id ,status =CouponRedemption .STATUS_PENDING 
        ).select_related ('discount_code').first ()
        if existing and existing .discount_code .code .upper ()==code_str :
            return Response ({
            'redemption_id':str (existing .id ),
            'order_id':str (order_id ),
            'discount_amount':str (existing .discount_amount ),
            'status':existing .status ,
            'message':'Existing coupon reservation retrieved.',
            },status =status .HTTP_200_OK )

        with transaction .atomic ():
            try :

                coupon =DiscountCode .objects .select_for_update ().get (
                code__iexact =code_str 
                )
            except DiscountCode .DoesNotExist :
                return Response ({'error':'Invalid coupon code.'},status =status .HTTP_404_NOT_FOUND )

            is_valid ,msg =coupon .is_valid (subtotal =subtotal ,customer_id =customer_id )
            if not is_valid :
                return Response ({'error':msg },status =status .HTTP_400_BAD_REQUEST )

            discount_amount =coupon .calculate_discount (subtotal )


            coupon .times_used +=1 
            coupon .save (update_fields =['times_used'])

            redemption =CouponRedemption .objects .create (
            discount_code =coupon ,
            order_id =order_id ,
            customer_id =customer_id ,
            discount_amount =discount_amount ,
            status =CouponRedemption .STATUS_PENDING ,
            )

        logger .info (
        f"[Coupon] Reserved {coupon .code } for order={order_id } "
        f"customer={customer_id } discount={discount_amount }"
        )
        return Response ({
        'redemption_id':str (redemption .id ),
        'order_id':str (order_id ),
        'discount_amount':str (discount_amount ),
        'status':redemption .status ,
        'message':'Coupon reserved successfully.',
        },status =status .HTTP_201_CREATED )


    @action (detail =False ,methods =['post'],url_path =r'confirm/(?P<order_id>[^/.]+)',
    permission_classes =[permissions .IsAuthenticated ])
    def confirm (self ,request ,order_id =None ):
        """Mark a PENDING coupon redemption as CONFIRMED after payment succeeds.

        Idempotent: calling again on an already-CONFIRMED record is a no-op.
        """
        try :
            oid =uuid .UUID (str (order_id ))
        except (ValueError ,AttributeError ):
            return Response ({'error':'Valid order_id (UUID) is required.'},status =status .HTTP_400_BAD_REQUEST )

        with transaction .atomic ():
            try :
                redemption =CouponRedemption .objects .select_for_update ().get (
                order_id =oid 
                )
            except CouponRedemption .DoesNotExist :
                return Response ({'error':'No coupon redemption found for this order.'},status =status .HTTP_404_NOT_FOUND )

            if redemption .status ==CouponRedemption .STATUS_CONFIRMED :
                return Response ({'status':'already_confirmed','order_id':str (oid )},status =status .HTTP_200_OK )

            if redemption .status ==CouponRedemption .STATUS_REVERSED :
                return Response ({'error':'Redemption has already been reversed.'},status =status .HTTP_409_CONFLICT )

            redemption .status =CouponRedemption .STATUS_CONFIRMED 
            redemption .save (update_fields =['status','updated_at'])

        logger .info (f"[Coupon] Confirmed redemption for order={oid }")
        return Response ({'status':'confirmed','order_id':str (oid )},status =status .HTTP_200_OK )


    @action (detail =False ,methods =['post'],url_path =r'reverse/(?P<order_id>[^/.]+)',
    permission_classes =[permissions .IsAuthenticated ])
    def reverse (self ,request ,order_id =None ):
        """Roll back a PENDING (or even CONFIRMED, for refunds) coupon redemption.

        Decrements times_used and marks the record REVERSED.
        Idempotent: repeated calls on an already-REVERSED record are safe.
        """
        try :
            oid =uuid .UUID (str (order_id ))
        except (ValueError ,AttributeError ):
            return Response ({'error':'Valid order_id (UUID) is required.'},status =status .HTTP_400_BAD_REQUEST )

        with transaction .atomic ():
            try :
                redemption =CouponRedemption .objects .select_for_update ().get (
                order_id =oid 
                )
            except CouponRedemption .DoesNotExist :

                return Response ({'status':'no_redemption','order_id':str (oid )},status =status .HTTP_200_OK )

            if redemption .status ==CouponRedemption .STATUS_REVERSED :
                return Response ({'status':'already_reversed','order_id':str (oid )},status =status .HTTP_200_OK )


            coupon =DiscountCode .objects .select_for_update ().get (
            pk =redemption .discount_code_id 
            )
            if coupon .times_used >0 :
                coupon .times_used -=1 
                coupon .save (update_fields =['times_used'])

            redemption .status =CouponRedemption .STATUS_REVERSED 
            redemption .save (update_fields =['status','updated_at'])

        logger .info (f"[Coupon] Reversed redemption for order={oid }")
        return Response ({'status':'reversed','order_id':str (oid )},status =status .HTTP_200_OK )

class ProductViewSet(FullBaseViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related('price_detail', 'category', 'subcategory').prefetch_related(
        'discounts', 'category__discounts', 'likes', 'variants', 'images', 'reviews'
    ).all()

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Product.objects.select_related('price_detail', 'category', 'subcategory').prefetch_related(
            'discounts', 'category__discounts', 'likes', 'variants', 'images', 'reviews'
        )
        user = getattr(self.request, 'user', None)

        parser_ctx = getattr(self.request, 'parser_context', {}) or {}
        is_detail_lookup = bool(parser_ctx and parser_ctx.get('kwargs', {}).get('pk'))
        category_id = self.request.query_params.get('category_id')
        subcategory_id = self.request.query_params.get('subcategory_id')
        param_tenant = self.request.query_params.get('tenant_id') or (None if is_detail_lookup else (hasattr(self.request, 'headers') and self.request.headers.get('X-Tenant-ID')))

        if category_id:
            qs = qs.filter(Q(category_id=category_id) | Q(subcategory__parent_id=category_id))
        if subcategory_id:
            qs = qs.filter(subcategory_id=subcategory_id)

        # Allow unauthenticated / public SAFE_METHODS browsing OR customer actions like 'like' & 'reviews'
        if getattr(self, 'action', None) in ['like', 'reviews'] or self.request.method in permissions.SAFE_METHODS or not (user and user.is_authenticated):
            if param_tenant and str(param_tenant).strip().upper() not in ['ALL', 'NONE', 'NULL', '']:
                qs = qs.filter(Q(tenant_id=param_tenant) | Q(tenant_id__isnull=True))
            return GeneralFilter.apply_filters(qs, self.request,
                search_fields=['name', 'description', 'sku'],
                default_ordering='-created_at')

        if _is_platform_admin(user):
            if param_tenant and str(param_tenant).strip().upper() not in ['ALL', 'NONE', 'NULL', '']:
                qs = qs.filter(tenant_id=param_tenant)
        else:
            user_tenant = getattr(user, 'tenant_id', None)
            if user_tenant:
                qs = qs.filter(tenant_id=user_tenant)
            else:
                if param_tenant and str(param_tenant).strip().upper() not in ['ALL', 'NONE', 'NULL', '']:
                    qs = qs.filter(Q(tenant_id=param_tenant) | Q(tenant_id__isnull=True))

        return GeneralFilter.apply_filters(qs, self.request,
            search_fields=['name', 'description', 'sku'],
            default_ordering='-created_at')


    def perform_create (self ,serializer ):
        tenant_id =getattr (self .request .user ,'tenant_id',None )
        product =serializer .save (tenant_id =tenant_id )

        try:
            from catalog.grpc_client import init_inventory_product
            stock_qty = self.request.data.get('initial_stock', 100)
            init_inventory_product(product_id_str=str(product.id), sku_str=getattr(product, 'sku', ''), quantity=int(stock_qty))
        except Exception:
            pass 

        try :
            import json 
            try :
                from kafka import KafkaProducer 
            except ImportError :
                from kafka_ng import KafkaProducer 

            producer =KafkaProducer (
            bootstrap_servers ='kafka:9092',
            value_serializer =lambda v :json .dumps (v ).encode ('utf-8')
            )
            event_payload ={
            "event_type":"product.created",
            "product_id":str (product .id ),
            "tenant_id":str (tenant_id )if tenant_id else None ,
            "name":product .name ,
            "description":product .description ,
            "price":float (product .base_price or 10.00 ),
            "polar_product_id":product .polar_product_id 
            }
            producer .send ('ecommerce-events',value =event_payload )
            producer .flush ()
        except Exception :
            pass 

        log_audit_event(
            self.request,
            action="product.created",
            resource_type="PRODUCT",
            resource_id=str(product.id),
            status="SUCCESS",
            details={"name": product.name, "sku": product.sku, "price": str(product.base_price)}
        )

    def perform_update(self, serializer):
        # serializer.instance is already the fetched object — no second get_object() needed
        product = serializer.save()
        log_audit_event(
            self.request,
            action="product.updated",
            resource_type="PRODUCT",
            resource_id=str(product.id),
            status="SUCCESS",
            details={"name": product.name, "sku": product.sku}
        )
        try:
            import json
            try:
                from kafka import KafkaProducer
            except ImportError:
                from kafka_ng import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            producer.send('ecommerce-events', value={
                "event_type": "product.updated",
                "product_id": str(product.id),
                "tenant_id": str(product.tenant_id) if product.tenant_id else None,
                "name": product.name,
                "description": product.description,
                "price": float(product.base_price or 10.00),
                "polar_product_id": product.polar_product_id
            })
            producer.flush()
        except Exception:
            pass

    def perform_destroy(self, instance):
        # Ownership already verified by IsTenantMember.has_object_permission
        log_audit_event(
            self.request,
            action="product.deleted",
            resource_type="PRODUCT",
            resource_id=str(instance.id),
            status="SUCCESS",
            details={"name": instance.name, "sku": instance.sku}
        )
        instance.delete()

    @action (detail =True ,methods =['patch','post'],permission_classes =[IsStoreOwnerOrPlatformAdmin ],url_path ='polar-id')
    def update_polar_id (self ,request ,pk =None ):
        product =self .get_object ()
        polar_id =request .data .get ('polar_product_id')
        if polar_id :
            product .polar_product_id =polar_id 
            product .save ()
            return Response ({'status':'updated','polar_product_id':polar_id },status =status .HTTP_200_OK )
        return Response ({'error':'polar_product_id required'},status =status .HTTP_400_BAD_REQUEST )

    @action (detail =True ,methods =['post'],permission_classes =[permissions .IsAuthenticated ])
    def like (self ,request ,pk =None ):
        product =self .get_object ()
        user_id =request .user .id 
        like ,created =ProductLike .objects .get_or_create (user_id =user_id ,product =product )
        if not created :
            like .delete ()
            return Response ({'status':'unliked'},status =status .HTTP_200_OK )
        try:
            import json, uuid
            try:
                from kafka import KafkaProducer
            except ImportError:
                from kafka_ng import KafkaProducer
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            producer.send('ecommerce-events', value={
                'event_id': str(uuid.uuid4()),
                'event_type': 'product.liked',
                'payload': {
                    'user_id': str(user_id),
                    'product_id': str(product.id),
                    'tenant_id': str(product.tenant_id) if product.tenant_id else None
                }
            })
            producer.flush()
        except Exception as e:
            logger.warning(f"Failed publishing product.liked to Kafka: {e}")
        return Response ({'status':'liked'},status =status .HTTP_201_CREATED )

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='deals')
    def deals(self, request):
        qs = self.get_queryset().filter(
            Q(discounts__is_active=True) | Q(category__discounts__is_active=True)
        ).distinct()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='bestsellers')
    def bestsellers(self, request):
        qs = self.get_queryset().annotate(likes_count_agg=Count('likes')).order_by('-likes_count_agg', '-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='new-arrivals')
    def new_arrivals(self, request):
        qs = self.get_queryset().order_by('-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class StorefrontProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public / Storefront endpoint for browsing products across stores/tenants.
    Read-only for all users (AllowAny).
    Can filter by tenant_id, category_id, subcategory_id, search, etc.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = Product.objects.select_related('price_detail', 'category', 'subcategory').prefetch_related(
            'discounts', 'category__discounts', 'likes', 'variants', 'images', 'reviews'
        ).all()

        tenant_id = self.request.query_params.get('tenant_id')
        category_id = self.request.query_params.get('category_id')
        subcategory_id = self.request.query_params.get('subcategory_id')

        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if category_id:
            qs = qs.filter(Q(category_id=category_id) | Q(subcategory__parent_id=category_id))
        if subcategory_id:
            qs = qs.filter(subcategory_id=subcategory_id)

        return GeneralFilter.apply_filters(qs, self.request,
            search_fields=['name', 'description', 'sku'],
            default_ordering='-created_at')


class StorefrontCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public / Storefront endpoint for browsing categories across stores/tenants.
    Read-only for all users (AllowAny).
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = CategorySerializer

    def get_queryset(self):
        qs = Category.objects.prefetch_related('subcategories').all()
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id:
            qs = qs.filter(Q(tenant_id=tenant_id) | Q(is_global=True) | Q(tenant_id__isnull=True))
        else:
            qs = qs.filter(Q(is_global=True) | Q(tenant_id__isnull=True))

        is_main = self.request.query_params.get('is_main')
        parent_id = self.request.query_params.get('parent')
        fetch_all = self.request.query_params.get('all') or self.request.query_params.get('fetch_all')

        if is_main is not None:
            qs = qs.filter(parent__isnull=True) if is_main.lower() == 'true' else qs.filter(parent__isnull=False)
        elif parent_id:
            qs = qs.filter(parent_id=parent_id)
        elif not (fetch_all and fetch_all.lower() == 'true') and not self.kwargs.get('pk') and self.action != 'retrieve':
            qs = qs.filter(parent__isnull=True)

        return GeneralFilter.apply_filters(qs, self.request, search_fields=['name', 'slug'], default_ordering='name')




