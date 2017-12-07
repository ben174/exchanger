import logging
import pprint

import flask
import requests
from requests.exceptions import HTTPError

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)


def quote(quote_quantity, action, from_currency, to_currency):
    actions = ('BUY', 'SELL')
    if action not in actions:
        raise ValueError('Invalid action, expected one of: {}'.format(actions))
    buy = action == 'BUY'

    book = 'asks' if buy else 'bids'
    url = 'https://api.gdax.com/products/{}-{}/book?level=2'
    data = None

    # try requesting data from exchange1 -> exchange2
    response = requests.get(url.format(from_currency, to_currency))
    if response.status_code == 404:
        logging.info('Exchange does not exist, reversing.')
        # first attempt failed, flip exchanges and try again
        buy = not buy
        # try requesting data from exchange2 -> exchange1
        response = requests.get(url.format(to_currency, from_currency))
        response.raise_for_status()
        if response.status_code == 404:
            raise Exception('Unable to resolve exchange between currencies.')

    data = response.json()

    logging.debug(pprint.pformat(data))
    quantity_allocated = 0.
    quantity_needed = quote_quantity
    weights = []
    logging.info('Quote total: {}'.format(quote_quantity))
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


# quote(20., 'BUY', 'BTC', 'USD')

# quote(20., 'SELL', 'USD', 'BTC') <- this is wrong
# quote(15000., 'SELL', 'BTC', 'USD')

# quote(1., 'BUY', 'BTC', 'USD')  # i want to buy one btc how much usd do i pay   (14000)
# quote(1., 'SELL', 'BTC', 'USD') # i want to sell one btc how much usd do i receive   (13000)
# quote(14000., 'BUY', 'USD', 'BTC')  # i want to buy 14000 usd how much btc do i pay (1)
# quote(14000., 'BUY', 'USD', 'BTC')  # i want to sell 14000 usd how much btc do i receive (1)

# quote(20., 'SELL', 'USD', 'BTC') <- this is wrong
quote(15000., 'BUY', 'USD', 'BTC')
