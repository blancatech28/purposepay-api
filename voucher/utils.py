from .models import Voucher

def update_expired_vouchers(vouchers):
    """Helper function to update the status of expired vouchers."""    
    for voucher in vouchers:
        voucher.update_status_if_expired()
    return vouchers

