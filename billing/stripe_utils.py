import stripe
from django.conf import settings
from .models import Subscription

# stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

def create_stripe_customer(company):
    """Creates a Stripe customer for the given company."""
    # try:
    #     customer = stripe.Customer.create(
    #         email=company.responsavel_email,
    #         name=company.razao_social,
    #         metadata={'company_id': company.id}
    #     )
    #     company.stripe_customer_id = customer.id
    #     company.save()
    #     return customer
    # except Exception as e:
    #     print(f"Error creating stripe customer: {e}")
    return None

def create_checkout_session(company, price_id):
    """Creates a Stripe checkout session for subscription."""
    # session = stripe.checkout.Session.create(
    #     customer=company.stripe_customer_id,
    #     payment_method_types=['card'],
    #     line_items=[{'price': price_id, 'quantity': 1}],
    #     mode='subscription',
    #     success_url=settings.SITE_URL + '/billing/success/',
    #     cancel_url=settings.SITE_URL + '/billing/cancel/',
    # )
    # return session
    return None

def sync_subscription_status(company_id, stripe_sub_id):
    """Syncs subscription status from Stripe to local database."""
    # sub = stripe.Subscription.retrieve(stripe_sub_id)
    # company = Company.objects.get(id=company_id)
    # company.subscription_status = sub.status
    # company.current_period_end = datetime.fromtimestamp(sub.current_period_end)
    # company.save()
    pass
