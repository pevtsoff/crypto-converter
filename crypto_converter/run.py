import click
from crypto_converter.aio_binance_api import quote_consumer_main
from crypto_converter.exchange_api import start_exchange_api


@click.group()
def cli():
    pass


@cli.command()
def quotes_consumer():
    print("inside quotes_consumer")
    quote_consumer_main()


@cli.command()
def api():
    start_exchange_api()


if __name__ == "__main__":
    cli()
