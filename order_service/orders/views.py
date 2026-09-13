import logging 
import requests 
from decimal import Decimal 
from uuid import UUID 
from django .db import transaction 
from rest_framework import generics ,permissions ,status 
from rest_framework .response import Response 
from rest_framework .views import APIView 

from common .filters import GeneralFilter 
from .models import Order ,OutboxEvent ,SubOrder ,OrderItem ,Shipping 
from .serializers import CreateOrderSerializer ,OrderSerializer ,OutboxEventSerializer 
from .grpc_client import get_catalog_product, check_inventory_stock 
from .utils import make_service_token 
from .checkout_lock import checkout_lock ,CheckoutLockError 

logger =logging .getLogger (__name__ )

class CreateOrderView (APIView ):
    permission_classes =[permissions .IsAuthenticated ]

    def post (self ,request ):
        serializer =CreateOrderSerializer (data =request .data )
        if not serializer .is_valid ():
            return Response (serializer .errors ,status =status .HTTP_400_BAD_REQUEST )

        customer_id =request .user .id 
        token_claims = getattr(request.user, 'token', {}) if hasattr(request.user, 'token') else {}

        product_id =serializer .validated_data .get ('product_id')
        quantity =serializer .validated_data .get ('quantity',1 )
        items_data =serializer .validated_data .get ('items',[])
        shipping_address =serializer .validated_data .get ('shipping_address',{})
        billing_address =serializer .validated_data .get ('billing_address',{})
        discount_code =serializer .validated_data .get ('discount_code')
        shipping_cost =Decimal (str (serializer .validated_data .get ('shipping_cost')or '0.00'))
        tax_amount =Decimal (str (serializer .validated_data .get ('tax_amount')or '0.00'))

        line_items =items_data if items_data else ([{'product_id':product_id ,'quantity':quantity }]if product_id else [])

        # Priority 1: Derive product owner tenant_id from line items or catalog service lookup
        tenant_id = None
        if line_items :
            for item in line_items :
                item_tenant = item.get('tenant_id')
                if item_tenant:
                    tenant_id = item_tenant
                    break
                pid = item.get('product_id')
                if pid:
                    try :
                        cat_res =requests .get (
                        f"http://catalog_service:8000/api/catalog/products/{pid }/",
                        headers ={'X-Service-Token':make_service_token ()},timeout =3 
                        )
                        if cat_res .status_code ==200 :
                            t_val = cat_res.json().get('tenant_id')
                            if t_val:
                                tenant_id = t_val
                                break
                    except Exception :
                        pass 

        # Priority 2: Request payload or header fallback
        if not tenant_id:
            tenant_id = (
                request .data .get ('tenant_id')
                or request .headers .get ('X-Tenant-ID')
                or request .META .get ('HTTP_X_TENANT_ID')
                or getattr (request .user ,'tenant_id',None )
                or token_claims.get('tenant_id')
            ) 


        # Self-Purchase Prevention Check
        user_tenant_id = str(getattr(request.user, 'tenant_id', '') or '')
        owned_tenant_ids = set([str(t) for t in token_claims.get('owned_tenant_ids', []) if t])
        if user_tenant_id:
            owned_tenant_ids.add(user_tenant_id)

        if owned_tenant_ids and line_items:
            for item in line_items:
                item_tenant = str(item.get('tenant_id') or '')
                if not item_tenant and item.get('product_id'):
                    try:
                        cat_res = requests.get(
                            f"http://catalog_service:8000/api/catalog/storefront/products/{item['product_id']}/",
                            headers={'X-Service-Token': make_service_token()}, timeout=3
                        )
                        if cat_res.status_code == 200:
                            item_tenant = str(cat_res.json().get('tenant_id', '') or '')
                    except Exception:
                        pass
                if item_tenant and item_tenant in owned_tenant_ids:
                    return Response(
                        {'error': 'Self-purchase prohibited: You cannot purchase products from a shop you own or manage.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        try :
            with checkout_lock (customer_id ):
                return self ._execute_checkout (
                request ,customer_id ,tenant_id ,line_items ,
                shipping_address ,billing_address ,discount_code ,
                shipping_cost ,tax_amount 
                )
        except CheckoutLockError as lock_err :
            return Response ({'error':str (lock_err )},status =status .HTTP_429_TOO_MANY_REQUESTS )

    def _execute_checkout (
    self ,request ,customer_id ,tenant_id ,line_items ,
    shipping_address ,billing_address ,discount_code ,
    shipping_cost ,tax_amount 
    ):
        auth_header =request .META .get ('HTTP_AUTHORIZATION','')
        service_token =make_service_token ()
        svc_headers ={
        'Authorization':auth_header ,
        'X-Service-Token':service_token ,
        'Content-Type':'application/json',
        'X-Tenant-Id':str (tenant_id )if tenant_id else '',
        }


        subtotal =Decimal ('0.00')
        processed_items =[]
        for item in line_items :
            pid =item ['product_id']
            qty =item ['quantity']
            unit_price =item .get ('unit_price')
            product_name =item .get ('product_name','')

            try :
                cat_resp =get_catalog_product (str (pid ))
                if not getattr (cat_resp ,'found',True ):
                    return Response (
                    {'error':f"Product '{pid }' does not exist in catalog."},
                    status =status .HTTP_404_NOT_FOUND 
                    )
                available_stock =getattr (cat_resp ,'stock_count',999999 )
                if available_stock <qty :
                    p_title =str (getattr (cat_resp ,'title',product_name or f"Product {pid }"))
                    return Response (
                    {'error':f"Product '{p_title }' is out of stock or has insufficient quantity available. Requested: {qty }, Available: {available_stock }"},
                    status =status .HTTP_400_BAD_REQUEST 
                    )
                # Only use catalog price as fallback — never override a client-supplied variant price
                if unit_price is None or unit_price == Decimal('0.00'):
                    unit_price =Decimal (str (getattr (cat_resp ,'price','10.00')))
                if not product_name :
                    product_name =str (getattr (cat_resp ,'title',f"Product {pid }"))
            except Exception as e :
                if '404'in str (e )or 'not found'in str (e ).lower ():
                    return Response ({'error':f"Product '{pid }' not found in catalog."},status =status .HTTP_404_NOT_FOUND )
                if unit_price is None or unit_price == Decimal('0.00') or not product_name :
                    return Response ({'error':'Catalog service unavailable for product check.'},status =status .HTTP_503_SERVICE_UNAVAILABLE )

            unit_price =Decimal (str (unit_price ))
            item_total =unit_price *Decimal (str (qty ))
            subtotal +=item_total 
            processed_items .append ({
            'product_id':pid ,
            'variant_id':item .get ('variant_id'),
            'variant_sku':item .get ('variant_sku') or item .get ('product_name',''),
            'product_name':product_name ,
            'unit_price':unit_price ,
            'quantity':qty ,
            'total_price':item_total ,
            })


        for p_item in processed_items:
            try:
                stock_res = check_inventory_stock(str(p_item['product_id']), p_item['quantity'])
                if not getattr(stock_res, 'is_available', True):
                    return Response(
                        {'error': getattr(stock_res, 'error_message', f"Product '{p_item['product_name']}' is out of stock.")},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as inv_grpc_err:
                logger.warning(f"[Checkout] gRPC stock check warning: {inv_grpc_err}")


        discount_amount =Decimal ('0.00')
        coupon_redeemed =False 
        redemption_order_id =None 

        if discount_code :
            try :
                val_resp =requests .post (
                'http://catalog_service:8000/api/catalog/coupons/validate/',
                json ={
                'code':discount_code ,
                'subtotal':str (subtotal ),
                },
                headers =svc_headers ,
                timeout =5 
                )
                if val_resp .status_code ==200 and val_resp .json ().get ('valid'):
                    discount_amount =Decimal (str (val_resp .json ().get ('discount_amount','0.00')))
                else :

                    self ._release_inventory (reserved_items ,svc_headers )
                    try :
                        msg =val_resp .json ().get ('message','Invalid coupon code.')
                    except Exception :
                        msg ='Invalid coupon code.'
                    return Response ({'error':msg },status =status .HTTP_400_BAD_REQUEST )
            except requests .exceptions .RequestException :

                logger .warning ("[Checkout] Catalog coupon validation unavailable; skipping discount.")
                discount_code =None 


        total_amount =max (subtotal +tax_amount +shipping_cost -discount_amount ,Decimal ('0.00'))


        with transaction .atomic ():
            order =Order .objects .create (
            tenant_id =tenant_id ,
            customer_id =customer_id ,
            product_id =line_items [0 ]['product_id']if line_items else None ,
            quantity =sum (i ['quantity']for i in line_items ),
            subtotal =subtotal ,
            tax_amount =tax_amount ,
            shipping_cost =shipping_cost ,
            discount_code =discount_code ,
            discount_amount =discount_amount ,
            total_amount =total_amount ,
            shipping_address =shipping_address ,
            billing_address =billing_address ,
            status ='PENDING',
            )

            suborder =SubOrder .objects .create (
            order =order ,
            vendor_id =tenant_id ,
            status ='PENDING',
            vendor_total =total_amount ,
            currency =order .currency ,
            )

            for p_item in processed_items :
                OrderItem .objects .create (
                order =order ,
                suborder =suborder ,
                product_id =p_item ['product_id'],
                variant_id =p_item ['variant_id'],
                product_name =p_item ['product_name'],
                variant_sku =p_item .get ('variant_sku',''),
                unit_price =p_item ['unit_price'],
                quantity =p_item ['quantity'],
                )

            if shipping_address :
                Shipping .objects .create (
                order =order ,
                suborder =suborder ,
                full_name =shipping_address .get ('full_name',getattr (request .user ,'username','Customer')),
                contact_phone =shipping_address .get ('phone_number',''),
                address_line_1 =shipping_address .get ('address_line_1','123 Main St'),
                address_line_2 =shipping_address .get ('address_line_2',''),
                city =shipping_address .get ('city','City'),
                state =shipping_address .get ('state',''),
                postcode =shipping_address .get ('postal_code','00000'),
                country =shipping_address .get ('country','USA'),
                shipping_cost =shipping_cost ,
                )

            outbox_payload ={
                'order_id':str (order .id ),
                'tenant_id':str (tenant_id )if tenant_id else None ,
                'customer_id':str (customer_id ),
                'total_amount':float (total_amount ),
                'subtotal':float (subtotal ),
                'discount_code':discount_code ,
                'discount_amount':float (discount_amount ),
                'status':order .status ,
                'items': [{'product_id': str(i['product_id']), 'quantity': i['quantity']} for i in line_items],
            }
            outbox_event =OutboxEvent .objects .create (
            event_type ='order.created',
            payload =outbox_payload ,
            status ='PENDING',
            )


        if discount_code :
            try :
                redeem_resp =requests .post (
                'http://catalog_service:8000/api/catalog/coupons/redeem/',
                json ={
                'code':discount_code ,
                'order_id':str (order .id ),
                'subtotal':str (subtotal ),
                },
                headers =svc_headers ,
                timeout =5 
                )
                if redeem_resp .status_code not in (200 ,201 ):
                    logger .error (
                    f"[Checkout] Coupon redeem API failed for order {order .id }: "
                    f"{redeem_resp .text }"
                    )
            except Exception as exc :
                logger .error (f"[Checkout] Could not call coupon redeem endpoint: {exc }")

        try :
            requests .post (
            'http://cart_service:8000/api/cart/clear/',
            headers =svc_headers ,
            timeout =5 
            )
            logger .info (f"[Checkout] Cart cleared for customer {customer_id }")
        except Exception as cart_err :
            logger .warning (f"[Checkout] Could not clear cart for customer {customer_id }: {cart_err }")

        logger .info (f"[Checkout] Order {order .id } created for customer {customer_id }")
        return Response ({
        'message':'Order created successfully and outbox event queued.',
        'order':OrderSerializer (order ).data ,
        'outbox_event_id':str (outbox_event .id ),
        },status =status .HTTP_201_CREATED )

    @staticmethod 
    def _release_inventory (reserved_items ,svc_headers ):
        """Best-effort release of already-reserved inventory items."""
        for item in reserved_items :
            try :
                requests .post (
                'http://inventory_service:8000/api/inventory/release/',
                json ={
                'product_id':str (item ['product_id']),
                'quantity':item ['quantity'],
                'reference_id':'CHECKOUT-ROLLBACK'
                },
                headers =svc_headers ,
                timeout =3 
                )
            except Exception :
                pass 

class InitiateOrderPaymentView (APIView ):
    permission_classes =[permissions .IsAuthenticated ]

    def post (self ,request ,order_id ):
        try :
            is_admin =getattr (request .user ,'is_superuser',False )or getattr (request .user ,'is_adminuser',False )
            if is_admin :
                order =Order .objects .get (id =order_id )
            else :
                order =Order .objects .get (id =order_id ,customer_id =request .user .id )
        except Order .DoesNotExist :
            return Response ({'error':'Order not found'},status =status .HTTP_404_NOT_FOUND )

        auth_header =request .META .get ('HTTP_AUTHORIZATION')
        service_token =make_service_token ()
        headers ={
        'Authorization':auth_header or '',
        'X-Service-Token':service_token ,
        'Content-Type':'application/json',
        }
        first_item =order .items .first ()
        prod_id =str (order .product_id )if order .product_id else (str (first_item .product_id )if first_item else None )
        prod_name =first_item .product_name if first_item else f"Order #{order .id }"

        payload ={
        'order_id':str (order .id ),
        'amount':str (order .total_amount ),
        'tenant_id':str (order .tenant_id )if order .tenant_id else None ,
        'product_id':prod_id ,
        'product_name':prod_name 
        }

        try :
            resp =requests .post ('http://payment_service:8000/api/payments/checkout/',json =payload ,headers =headers ,timeout =20 )
            if resp .status_code in [200 ,201 ]:
                data =resp .json ()
                order .polar_checkout_id =data .get ('payment',{}).get ('polar_checkout_id')
                if data .get ('status')=='PAID'or data .get ('payment',{}).get ('status')=='PAID':
                    order .status ='PAID'
                    order .suborders .update (status ='PAID')
                order .save ()
                return Response (data ,status =resp .status_code )
            else :
                return Response ({'error':'Payment service error','details':resp .text },status =resp .status_code )
        except Exception as e :
            return Response ({'error':f'Failed to communicate with payment_service: {str (e )}'},status =status .HTTP_503_SERVICE_UNAVAILABLE )

class OutboxListView (generics .ListAPIView ):
    permission_classes =[permissions .IsAuthenticated ]
    serializer_class =OutboxEventSerializer 

    def get_queryset(self):
        user = self.request.user
        is_super = (
            getattr(user, 'is_superuser', False)
            or getattr(user, 'is_adminuser', False)
        )
        if is_super:
            qs = OutboxEvent.objects.all()
        else:
            tenant_id = getattr(user, 'tenant_id', None)
            if tenant_id:
                qs = OutboxEvent.objects.filter(payload__tenant_id=str(tenant_id))
            else:
                qs = OutboxEvent.objects.none()
        return GeneralFilter.apply_filters(qs, self.request, filter_map={'status': 'status'}, default_ordering='-created_at')

class CancelOrderView (APIView ):
    permission_classes =[permissions .IsAuthenticated ]

    def post (self ,request ,order_id ):
        try :
            order =Order .objects .get (id =order_id )
        except Order .DoesNotExist :
            return Response ({'error':'Order not found'},status =status .HTTP_404_NOT_FOUND )

        is_admin = getattr(request.user, 'is_superuser', False) or getattr(request.user, 'is_platform_admin', False) or (str(getattr(request.user, 'role', '')).upper() in ['PLATFORM_ADMIN', 'SUPERADMIN'])
        is_customer_owner = str(order.customer_id) == str(request.user.id)
        user_tenant = str(getattr(request.user, 'tenant_id', '') or '')
        is_tenant_staff = bool(user_tenant and order.tenant_id and user_tenant == str(order.tenant_id))

        if not (is_admin or is_customer_owner or is_tenant_staff):
            return Response ({'error':'Permission denied'},status =status .HTTP_403_FORBIDDEN )


        if order .status =='CANCELLED':
            return Response ({
            'message':'Order is already cancelled',
            'order':OrderSerializer (order ).data 
            },status =status .HTTP_200_OK )

        if order .status not in ['PENDING','PAID']:
            return Response (
            {'error':f'Order cannot be cancelled in status {order .status }'},
            status =status .HTTP_400_BAD_REQUEST 
            )

        auth_header =request .META .get ('HTTP_AUTHORIZATION','')
        service_token =make_service_token ()
        svc_headers ={
        'Authorization':auth_header ,
        'X-Service-Token':service_token ,
        'Host':'localhost',
        'Content-Type':'application/json',
        'X-Tenant-Id':str (order .tenant_id )if order .tenant_id else '',
        }

        with transaction .atomic ():
            order .status ='CANCELLED'
            order .save ()
            order .suborders .update (status ='CANCELLED')


            for item in order .items .all ():
                try :
                    requests .post (
                    'http://inventory_service:8000/api/inventory/release/',
                    json ={
                    'product_id':str (item .product_id ),
                    'quantity':item .quantity ,
                    'reference_id':f"CANCEL-{order .id }"
                    },
                    headers =svc_headers ,
                    timeout =3 
                    )
                except Exception :
                    pass 

            outbox_payload ={
            'order_id':str (order .id ),
            'tenant_id':str (order .tenant_id )if order .tenant_id else None ,
            'customer_id':str (order .customer_id ),
            'status':'CANCELLED',
            }
            OutboxEvent .objects .create (
            event_type ='order.cancelled',
            payload =outbox_payload ,
            status ='PENDING',
            )


        if order .discount_code :
            try :
                requests .post (
                f'http://catalog_service:8000/api/catalog/coupons/reverse/{order .id }/',
                headers =svc_headers ,
                timeout =5 
                )
            except Exception as exc :
                logger .warning (f"[CancelOrder] Could not reverse coupon for order {order .id }: {exc }")

        return Response ({
        'message':'Order cancelled successfully',
        'order':OrderSerializer (order ).data 
        },status =status .HTTP_200_OK )

class DispatchOrderView (APIView ):
    permission_classes =[permissions .IsAuthenticated ]

    def post (self ,request ,order_id ):
        try :
            order =Order .objects .get (id =order_id )
        except Order .DoesNotExist :
            return Response ({'error':'Order not found'},status =status .HTTP_404_NOT_FOUND )

        user =request .user 
        is_admin =getattr (user ,'is_superuser',False )or getattr (user ,'is_adminuser',False )
        user_tenant =getattr (user ,'tenant_id',None )
        user_role =str (getattr (user ,'role','')or '').lower ()

        is_owner_of_order = bool(user_tenant and order.tenant_id and str(user_tenant) == str(order.tenant_id))
        if not (is_admin or is_owner_of_order):
            return Response({'error': 'Permission denied. Only shop owners/admins can dispatch orders.'}, status=status.HTTP_403_FORBIDDEN)

        if order .status in ['SHIPPED','DELIVERED','DISPATCHED']:
            return Response ({
            'message':'Order is already dispatched/shipped',
            'order':OrderSerializer (order ).data 
            },status =status .HTTP_200_OK )

        if order .status =='CANCELLED':
            return Response ({'error':'Cannot dispatch a cancelled order'},status =status .HTTP_400_BAD_REQUEST )

        carrier =request .data .get ('carrier')or 'Standard Delivery'
        tracking_code =request .data .get ('tracking_code')

        with transaction .atomic ():
            from django .utils import timezone 
            now =timezone .now ()
            order .status ='SHIPPED'
            order .save ()

            for sub in order .suborders .all ():
                sub .status ='SHIPPED'
                sub .shipped_at =now 
                sub .save ()

            shipping = Shipping.objects.filter(order=order).first()
            if not shipping:
                addr = order.shipping_address or {}
                shipping = Shipping.objects.create(
                    order=order,
                    full_name=addr.get('full_name', 'Customer'),
                    address_line_1=addr.get('address_line_1', 'Main St'),
                    city=addr.get('city', 'City'),
                    postcode=addr.get('postal_code', '00000'),
                    country=addr.get('country', 'USA'),
                    carrier=carrier,
                    status='SHIPPED',
                    shipped_at=now
                )
                if tracking_code:
                    shipping.tracking_code = tracking_code
                    shipping.save()
            else:
                shipping.carrier = carrier
                shipping.status = 'SHIPPED'
                if tracking_code:
                    shipping.tracking_code = tracking_code
                shipping.shipped_at = now
                shipping.save()

            from .models import StatusHistory
            StatusHistory.objects.create(
                entity_type='shipping',
                entity_id=shipping.id,
                from_status='PREPARING',
                to_status='SHIPPED',
                changed_by=request.user.id,
                notes=f"Order dispatched via {carrier}"
            )



            auth_header =request .META .get ('HTTP_AUTHORIZATION')
            service_token =make_service_token ()
            headers ={
            'Authorization':auth_header or '',
            'X-Service-Token':service_token ,
            'Host':'localhost',
            'Content-Type':'application/json',
            'X-Tenant-Id':str (order .tenant_id )if order .tenant_id else ''
            }

            items =order .items .all ()
            for item in items :
                try :
                    commit_payload ={
                    'product_id':str (item .product_id ),
                    'quantity':item .quantity ,
                    'reference_id':f"DISPATCH-{order .id }"
                    }
                    requests .post (
                    'http://inventory_service:8000/api/inventory/commit/',
                    json =commit_payload ,
                    headers =headers ,
                    timeout =5 
                    )
                except Exception as inv_err :
                    import logging 
                    logging .getLogger (__name__ ).warning (f"Could not commit inventory stock for item {item .product_id }: {inv_err }")

            outbox_payload ={
            'order_id':str (order .id ),
            'tenant_id':str (order .tenant_id )if order .tenant_id else None ,
            'customer_id':str (order .customer_id ),
            'status':'SHIPPED',
            'tracking_code':shipping .tracking_code if shipping else None ,
            'carrier':shipping .carrier if shipping else None 
            }
            OutboxEvent .objects .create (
            event_type ='order.shipped',
            payload =outbox_payload ,
            status ='PENDING'
            )

        return Response ({
        'message':'Order dispatched successfully and stock committed in inventory',
        'order':OrderSerializer (order ).data 
        },status =status .HTTP_200_OK )

class MarkOrderPaidView (APIView ):
    permission_classes =[permissions .IsAuthenticated ]

    def post (self ,request ,order_id ):
        try :
            order =Order .objects .get (id =order_id )
        except Order .DoesNotExist :
            return Response ({'error':'Order not found'},status =status .HTTP_404_NOT_FOUND )

        is_admin =getattr (request .user ,'is_superuser',False )or getattr (request .user ,'is_adminuser',False )
        service_token = request.META.get('HTTP_X_SERVICE_TOKEN') or request.headers.get('X-Service-Token')
        expected_token = make_service_token()
        service_token_valid = bool(service_token and service_token == expected_token)
        user_tenant =getattr (request .user ,'tenant_id',None )
        if not is_admin and not service_token_valid and (not user_tenant or str (user_tenant )!=str (order .tenant_id )):
            return Response ({'error':'Permission denied'},status =status .HTTP_403_FORBIDDEN )

        with transaction .atomic ():
            order .status ='PAID'
            order .save ()
            order .suborders .update (status ='PAID')


            auth_header =request .META .get ('HTTP_AUTHORIZATION')
            service_token =make_service_token ()
            headers ={
            'Authorization':auth_header or '',
            'X-Service-Token':service_token ,
            'Content-Type':'application/json'
            }
            fin_payload ={
            'order_id':str (order .id ),
            'customer_id':str (order .customer_id ),
            'tenant_id':str (order .tenant_id )if order .tenant_id else None ,
            'total_amount':str (order .total_amount )
            }
            try :
                requests .post ('http://finance_service:8000/api/finance/ledger/record-payment/',json =fin_payload ,headers =headers ,timeout =5 )
            except Exception :
                pass 

        return Response ({
        'message':'Order marked as PAID and finance ledger recorded',
        'order':OrderSerializer (order ).data 
        },status =status .HTTP_200_OK )

class OrderListView (generics .ListAPIView ):
    permission_classes =[permissions .IsAuthenticated ]
    serializer_class =OrderSerializer 

    def get_queryset (self ):
        qs = Order.objects.prefetch_related('items', 'shipments', 'suborders', 'suborders__items', 'suborders__shipments').distinct()
        user = self.request.user 
        token_claims = getattr(user, 'token', {}) if hasattr(user, 'token') else {}

        is_platform_admin = (
            getattr(user, 'is_superuser', False)
            or getattr(user, 'is_adminuser', False)
            or token_claims.get('is_superuser', False)
            or token_claims.get('is_adminuser', False)
            or token_claims.get('is_platform_admin', False)
            or str(getattr(user, 'role', '') or '').upper() == 'PLATFORM_ADMIN'
        )

        header_tenant = (
            self.request.headers.get('X-Tenant-ID')
            or self.request.META.get('HTTP_X_TENANT_ID')
            or self.request.query_params.get('tenant_id')
        )

        scope = self.request.query_params.get('scope', '').lower()
        portal_type = (
            self.request.headers.get('X-Portal-Type')
            or self.request.headers.get('X-Admin-Portal')
            or self.request.META.get('HTTP_X_PORTAL_TYPE')
            or self.request.META.get('HTTP_X_ADMIN_PORTAL')
            or ''
        ).lower()

        if scope in ['customer', 'my_orders', 'storefront'] or portal_type == 'storefront':
            qs = qs.filter(customer_id=user.id)
        elif is_platform_admin:
            if header_tenant and header_tenant.strip().upper() not in ['ALL', 'NONE', 'NULL', '']:
                target_tenant = header_tenant.strip()
                from django.db.models import Q 
                qs = qs.filter(Q(tenant_id=target_tenant) | Q(suborders__vendor_id=target_tenant) | Q(tenant_id__isnull=True))
        else:
            # Regular Shop Owner / Vendor: Strict Tenant Isolation
            user_tenant_id = getattr(user, 'tenant_id', None) or token_claims.get('tenant_id')
            memberships = token_claims.get('memberships', [])
            user_tenant_ids = set()
            if user_tenant_id:
                user_tenant_ids.add(str(user_tenant_id))
            for m in memberships:
                if isinstance(m, dict) and m.get('tenant_id'):
                    user_tenant_ids.add(str(m['tenant_id']))

            if header_tenant and header_tenant.strip().upper() not in ['ALL', 'NONE', 'NULL', '']:
                requested_tenant = header_tenant.strip()
                if not user_tenant_ids or requested_tenant in user_tenant_ids:
                    target_tenants = [requested_tenant]
                else:
                    return Order.objects.none()
            elif user_tenant_ids:
                target_tenants = list(user_tenant_ids)
            else:
                target_tenants = None

            if target_tenants:
                from django.db.models import Q 
                qs = qs.filter(Q(tenant_id__in=target_tenants) | Q(suborders__vendor_id__in=target_tenants))
            else:
                qs = qs.filter(customer_id=user.id)

        filter_map = {'status': 'status', 'customer_id': 'customer_id', 'product_id': 'product_id', 'tenant_id': 'tenant_id'}
        return GeneralFilter.apply_filters(qs, self.request, filter_map=filter_map, default_ordering='-created_at')

class OrderDetailView (generics .RetrieveAPIView ):
    permission_classes =[permissions .IsAuthenticated ]
    serializer_class =OrderSerializer 
    lookup_field ='id'
    lookup_url_kwarg ='order_id'

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset (self ):
        qs = Order.objects.prefetch_related('items', 'shipments', 'suborders', 'suborders__items', 'suborders__shipments').distinct()
        user = self.request.user
        if not user or not user.is_authenticated:
            return Order.objects.none()

        token_claims = getattr(user, 'token', {}) if hasattr(user, 'token') else {}

        is_platform_admin = (
            getattr(user, 'is_superuser', False)
            or getattr(user, 'is_adminuser', False)
            or token_claims.get('is_superuser', False)
            or token_claims.get('is_adminuser', False)
            or token_claims.get('is_platform_admin', False)
            or str(getattr(user, 'role', '') or '').upper() == 'PLATFORM_ADMIN'
        )
        portal_type = (
            self.request.headers.get('X-Portal-Type')
            or self.request.headers.get('X-Admin-Portal')
            or self.request.META.get('HTTP_X_PORTAL_TYPE')
            or self.request.META.get('HTTP_X_ADMIN_PORTAL')
            or ''
        ).lower()

        if portal_type == 'storefront':
            qs = qs.filter(customer_id=user.id)
        elif is_platform_admin:
            pass
        else:
            user_tenant_id = getattr(user, 'tenant_id', None) or token_claims.get('tenant_id')
            memberships = token_claims.get('memberships', [])
            user_tenant_ids = set()
            if user_tenant_id:
                user_tenant_ids.add(str(user_tenant_id))
            for m in memberships:
                if isinstance(m, dict) and m.get('tenant_id'):
                    user_tenant_ids.add(str(m['tenant_id']))

            from django.db.models import Q 
            if user_tenant_ids:
                qs = qs.filter(Q(tenant_id__in=user_tenant_ids) | Q(suborders__vendor_id__in=user_tenant_ids) | Q(customer_id=user.id))
            else:
                qs = qs.filter(customer_id=user.id)
        return qs 


class BroadcastNotificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_ids = request.data.get('user_ids', [])
        tenant_id = request.data.get('tenant_id')
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'SYSTEM')
        metadata = request.data.get('metadata', {})

        if not (title and message):
            return Response({'error': 'title and message are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            import json, os
            try:
                from kafka import KafkaProducer
            except ImportError:
                from kafka_ng import KafkaProducer

            bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'))
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            event_data = {
                'event_type': 'notification.broadcast',
                'payload': {
                    'recipient_ids': user_ids,
                    'tenant_id': tenant_id,
                    'title': title,
                    'message': message,
                    'notification_type': notification_type,
                    'metadata': metadata
                }
            }
            producer.send('notifications', event_data)
            producer.flush()
            producer.close()
        except Exception as e:
            logger.error(f"Failed to publish notification to Kafka: {e}")

        return Response({'status': 'broadcast triggered via Kafka'}, status=status.HTTP_200_OK)
 

