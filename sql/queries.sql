select * from binance_tickers_list btl
select count(*) from binance_tickers_list btl


delete from binance_tickers_list btl

select * from binance_tickers_data
select count(*) from binance_tickers_data

delete from alembic_version

select * from binance_tickers_aggregated_data btad
where ticker_id=3



select * from binance_tickers_list btl
inner join binance_tickers_data btad on btl.id=btad.ticker_id
where btl.ticker_name='btcusdt'

select * from binance_tickers_list btl
inner join binance_tickers_aggregated_data btad on btl.id=btad.ticker_id
where btl.ticker_name='btcusdt'


select btl.ticker_name , btad."timestamp" , btad.price, AVG(btad.price::FLOAT) over (ORDER BY btad."timestamp" ROWS BETWEEN 9 PRECEDING AND CURRENT ROW) from binance_tickers_list btl
inner join binance_tickers_data btad on btl.id=btad.ticker_id
where btl.ticker_name='btcusdt'
order by btad."timestamp"