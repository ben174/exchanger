# exchanger
Stub endpoint for testing

http://127.0.0.1:5000/quote -d '{"action":"buy", "base_currency":"btc", "quote_currency":"usd", "amount": "3.00000"}' -X POST -H "Content-Type: application/json"                                                                                                          
{
"currency": "USD",
"price": 14055.01,
"total": 42165.03
}
http://127.0.0.1:5000/quote -d '{"action":"buy", "base_currency":"usd", "quote_currency":"btc", "amount": "3.00000"}' -X POST -H "Content-Type: application/json"
