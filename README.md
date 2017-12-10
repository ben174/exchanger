# Exchanger

Had to timebox myself to a total of two hours on this, due to other homework assignments
and day to day work. So I was unfortunately unable to complete this as well as I'd like:

The first things I'd change:

* Unit Testing
* Refactor (for easier unit testing)
* Endpoint tests
* Stub out endpoints for testing
* Resolve the requirement: "It should also be able to support trades where the base and quote currencies are the inverse of a GDAX trading pair."
  * I put a lot of thought into this, and couldn't quite make out how to do this without a baseline quote for the quote_currency.
    Of course I didn't just want to take the top quote off the order book, but didn't want to reach out to another API for market price.
    In the time I limited myself, I decided to submit what I had :(


# Run it:

Install requirements:
    pip install -r requirements.txt

Or simply:

    pip install flask

Start the server:

    export FLASK_APP=quote.py
    flask run

# Usage

    http://127.0.0.1:5000/quote -d '{"action":"buy", "base_currency":"btc", "quote_currency":"usd", "amount": "3.00000"}' -X POST -H "Content-Type: application/json"                                                                                                          
    {
    "currency": "USD",
    "price": 14055.01,
    "total": 42165.03
    }
