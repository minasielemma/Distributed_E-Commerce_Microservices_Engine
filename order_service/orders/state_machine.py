"""
State Machine implementation for Order and Shipping lifecycles.
Enforces valid state transitions and strictly prevents shipping unpaid orders.
"""

class InvalidStateTransitionError(Exception):
    def __init__(self, current_status, target_status, reason=None):
        self.current_status = current_status
        self.target_status = target_status
        self.reason = reason or f"Cannot transition status from '{current_status}' to '{target_status}'."
        super().__init__(self.reason)


class OrderState:
    PENDING = 'PENDING'
    PAID = 'PAID'
    PROCESSING = 'PROCESSING'
    SHIPPED = 'SHIPPED'
    DELIVERED = 'DELIVERED'
    CANCELLED = 'CANCELLED'
    FAILED = 'FAILED'
    REFUNDED = 'REFUNDED'


class OrderStateMachine:
    """
    State machine enforcing valid state transitions for Orders.
    
    Rule: Unpaid orders (status PENDING or FAILED) CANNOT be shipped or dispatched.
    """
    
    ALLOWED_TRANSITIONS = {
        OrderState.PENDING: {OrderState.PAID, OrderState.CANCELLED, OrderState.FAILED},
        OrderState.PAID: {OrderState.PROCESSING, OrderState.SHIPPED, OrderState.CANCELLED, OrderState.REFUNDED},
        OrderState.PROCESSING: {OrderState.SHIPPED, OrderState.CANCELLED, OrderState.REFUNDED},
        OrderState.SHIPPED: {OrderState.DELIVERED, OrderState.CANCELLED, OrderState.REFUNDED},
        OrderState.DELIVERED: {OrderState.REFUNDED},
        OrderState.CANCELLED: set(),
        OrderState.FAILED: set(),
        OrderState.REFUNDED: set(),
    }

    @classmethod
    def can_transition(cls, current_status: str, target_status: str) -> bool:
        if current_status == target_status:
            return True
        allowed = cls.ALLOWED_TRANSITIONS.get(current_status, set())
        return target_status in allowed

    @classmethod
    def validate_transition(cls, order, target_status: str):
        current_status = getattr(order, 'status', current_status if isinstance(order, str) else '')
        if current_status == target_status:
            return

        # Strict business rule enforcement: Unpaid order must not be shipped
        if target_status in [OrderState.SHIPPED, OrderState.DELIVERED] and current_status in [OrderState.PENDING, OrderState.FAILED]:
            order_id_str = f" {getattr(order, 'id', '')}" if hasattr(order, 'id') else ""
            raise InvalidStateTransitionError(
                current_status,
                target_status,
                reason=f"Unpaid order{order_id_str} cannot be shipped. Current status is '{current_status}'. Order must be PAID before shipping."
            )

        if not cls.can_transition(current_status, target_status):
            order_id_str = f" {getattr(order, 'id', '')}" if hasattr(order, 'id') else ""
            raise InvalidStateTransitionError(
                current_status,
                target_status,
                reason=f"Invalid state transition: Cannot transition order{order_id_str} from '{current_status}' to '{target_status}'."
            )

    @classmethod
    def transition(cls, order, target_status: str, save: bool = True):
        cls.validate_transition(order, target_status)
        order.status = target_status
        if save and hasattr(order, 'save'):
            order.save(update_fields=['status', 'updated_at'])
        return order
