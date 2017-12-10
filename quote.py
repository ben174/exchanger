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
    if action not in actions:
        raise ValueError('Invalid action, expected one of: {}'.format(actions))
    buy = action == 'BUY'

    book = 'asks' if buy else 'bids'
    url = 'https://api.gdax.com/products/{}-{}/book?level=2'

    data = None

    # try requesting data from exchange1 -> exchange2
    response = requests.get(url.format(base_currency, quote_currency))
    if response.status_code == 404:
        # first attempt failed, flip exchanges and try again
        logging.info('Exchange does not exist, reversing.')

        # i believe we'd switch tables here (i.e. asks <-> bids)
        buy = not buy

        # try requesting data from exchange2 -> exchange1
        # could probably have checked another api for what
        # exchanges are available, but the spec only listed
        # a single endpoint
        response = requests.get(url.format(quote_currency, base_currency))
        response.raise_for_status()
        if response.status_code == 404:
            raise Exception('Unable to resolve exchange between currencies.')

        # never got a working solution to flipping currencies
        # seems like I'd need a baseline quote to flip from
        # maybe this endpoint would solve it?
        # https://api.gdax.com/products/BTC-USD/ticker
        # but again, the spec only listed the single endpoint
        raise NotImplementedError('Sorry :(')

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

    return {
        'total': total_cost,
        'price': unit_average,
        'currency': quote_currency,
    }


if __name__ == '__main__':
    print quote(1., 'BUY', 'BTC', 'USD')
