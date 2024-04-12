from bot.arbitrage_bot import Arbitrage_bot

if __name__ == '__main__':
    print("ARBITRAGE BOT\n"
          "This bot searches for arbitrage opportunities between Binance and Bybit exchanges. It examines BTCUSDT "
          "and ETHUSDT cryptocurrency pairs and searches for profitable arbitrages every 10 seconds. After every"
          "10 cycles, the current stage of the portfolio is displayed with the percentual change for each held asset.\n"
          "If you wish to stop the execution of the bot, please press ESC.\n")

    currency_pairs = ["BTCUSDT", "ETHUSDT"]
    try:
        Arbitrage_bot(currency_pairs)
    except ValueError:
        quit()
