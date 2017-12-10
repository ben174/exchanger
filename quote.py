import logging
import pprint

from flask import Flask, jsonify, request
import requests


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
app = Flask(__name__)


@app.route('/quote', methods=['POST'])
def endpoint():
    required_fields = ('amount', 'action', 'base_currency', 'quote_currency')
    if not all([f in request.json for f in required_fields]):
        raise ValueError('Missing one of required fields: {}'.format(
            ', '.join(required_fields)
        ))
    quantity = float(request.json.get('amount'))
    action = request.json.get('action').upper()
    base_currency = request.json.get('base_currency').upper()
    quote_currency = request.json.get('quote_currency').upper()
    return jsonify(quote(quantity, action, base_currency, quote_currency))


def quote(quote_quantity, action, base_currency, quote_currency):
    actions = ('BUY', 'SELL')
    inverted = False
    if action not in actions:
        raise ValueError('Invalid action, expected one of: {}'.format(actions))
    buy = action == 'BUY'

    book = 'asks' if buy else 'bids'
    url = 'https://api.gdax.com/products/{}-{}/book?level=2'

    data = None

    # try requesting data from exchange1 -> exchange2
    response = requests.get(url.format(base_currency, quote_currency))
    if response.status_code == 404:
        logging.info('Exchange does not exist, reversing.')
        # need a quote price to reverse the exchange
        quote_url = 'https://api.gdax.com/products/{}-{}/ticker'
        response = requests.get(quote_url.format(quote_currency, base_currency))
        quote = float(response.json()['bid'])
        quote_quantity = quote_quantity / quote

        # first attempt failed, flip exchanges and try again
        buy = not buy
        inverted = True
        # try requesting data from exchange2 -> exchange1
        response = requests.get(url.format(quote_currency, base_currency))
        response.raise_for_status()
        if response.status_code == 404:
            raise Exception('Unable to resolve exchange between currencies.')

    data = response.json()

    logging.debug(pprint.pformat(data))
    quantity_allocated = 0.
    quantity_needed = quote_quantity
    weights = []
    logging.info('Quote total: {}'.format(quote_quantity))
    logging.debug('Consulting table: {}'.format(book))
    for price, quantity_available, _ in data[book]:
        # determine amount to purchase
        price, quantity_available = float(price), float(quantity_available)
        logging.info('Allocated: {}, Sill Needed: {}'.format(
            quantity_allocated,
            quantity_needed
        ))
        logging.info('Aggregate Price: {}, Quantity Available: {}'.format(
            price,
            quantity_available
        ))
        quantity_to_purchase = min(quantity_needed, quantity_available)

        # determine percent of purchase
        percent_of_purchase = quantity_to_purchase / quote_quantity
        logging.info('Allocating {} at {} ({}%)'.format(
            quantity_to_purchase,
            price,
            round(percent_of_purchase * 100, 1),
        ))

        # collect weights
        weights.append((price, percent_of_purchase))
        quantity_allocated += quantity_to_purchase
        quantity_needed = quote_quantity - quantity_allocated

        if quantity_allocated == quote_quantity:
            break

    if quantity_allocated != quote_quantity:
        raise Exception('Not enough data available to allocate purchase.')

    # ensure we totaled 100%, quick sanity check - not for production
    if not (sum([p[1] for p in weights]) == 1):
        # TODO: Figure out
        logging.warning('Rounding error, probably')

    # use collected weights to compute total cost and average
    # (could have done this in the loop above, but for clarity it's split)
    total_cost = 0.
    for price, percent in weights:
        cost = percent * (price * quote_quantity)
        logging.info('Allocating {}% @ {}: {}'.format(
            round(percent * 100, 1),
            price,
            cost,
        ))
        total_cost += cost
    unit_average = total_cost / quote_quantity
    logging.info('Total cost: {}, (Average Unit Price: {})'.format(
        total_cost,
        unit_average,
    ))

    if inverted:
        '''
        Quantity 3
        I have:
        {
          "currency": "BTC",
          "price": 14046.01,
          "total": 42138.03
        }

        I want:
        {
          "currency": "BTC",
          "price": 14046.01,
          "total": 42138.03
        }
        '''

    return {
        'total': total_cost,
        'price': unit_average,
        'currency': quote_currency,
    }

# print quote(3., 'BUY', 'BTC', 'USD')
# print quote(2., 'BUY', 'BTC', 'USD')
print quote(1000., 'BUY', 'USD', 'BTC')
