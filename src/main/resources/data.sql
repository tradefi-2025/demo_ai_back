-- Insertion des features
INSERT INTO feature (name, description)
VALUES ('Support',
        'A price level where a stock tends to find buying interest, preventing it from falling further. It''s considered a ''floor'' that the price struggles to break below.'),
       ('Resistance',
        'A price level where a stock encounters selling interest, preventing it from rising further. It''s considered a ''ceiling'' that the price struggles to break above.'),
       ('Simple Moving Average (SMA)',
        'The average price of a stock over a specific time period, used to smooth out price data and identify trends.'),
       ('Exponential Moving Average (EMA)', 'A type of moving average that gives more weight to recent prices.'),
       ('MACD (Moving Average Convergence Divergence)',
        'A technical indicator that helps investors identify price trends, measure trend momentum, and identify entry points for buying or selling.'),
       ('Bollinger Bands', 'A technical analysis tool that helps investors and traders understand market volatility.'),
       ('Relative Strength Index (RSI)',
        'RSI measures the speed and magnitude of a security''s recent price changes to detect overbought or oversold conditions. It can signal when to buy and sell, typically considering RSI > 70 as overbought and RSI < 30 as oversold.'),
       ('Stochastic Oscillator',
        'A momentum indicator comparing the closing price of a security to its price range over a period, used to generate overbought and oversold signals.'),
       ('Price Rate of Change (ROC) Indicator',
        'A momentum-based technical indicator that measures the percentage change in price between the current price and the price a certain number of periods ago.');

-- Support
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'lookback_period', '20', 'INTEGER', false, id
FROM feature
WHERE name = 'Support';

-- Resistance
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'lookback_period', '20', 'INTEGER', false, id
FROM feature
WHERE name = 'Resistance';

-- SMA
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period', '', 'INTEGER', true, id
FROM feature
WHERE name = 'Simple Moving Average (SMA)';

-- EMA
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period', '', 'INTEGER', true, id
FROM feature
WHERE name = 'Exponential Moving Average (EMA)';

-- MACD
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'short_period', '12', 'INTEGER', false, id
FROM feature
WHERE name = 'MACD (Moving Average Convergence Divergence)';
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'long_period', '26', 'INTEGER', false, id
FROM feature
WHERE name = 'MACD (Moving Average Convergence Divergence)';

-- Bollinger Bands
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period', '20', 'INTEGER', false, id
FROM feature
WHERE name = 'Bollinger Bands';
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'num_std_dev', '2.0', 'DOUBLE', false, id
FROM feature
WHERE name = 'Bollinger Bands';
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'band', 'middle', 'STRING', false, id
FROM feature
WHERE name = 'Bollinger Bands';

-- RSI
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period', '14', 'INTEGER', false, id
FROM feature
WHERE name = 'Relative Strength Index (RSI)';

-- Stochastic Oscillator
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period', '14', 'INTEGER', false, id
FROM feature
WHERE name = 'Stochastic Oscillator';
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'k_smoothing', '3', 'INTEGER', false, id
FROM feature
WHERE name = 'Stochastic Oscillator';
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'd_smoothing', '3', 'INTEGER', false, id
FROM feature
WHERE name = 'Stochastic Oscillator';

-- ROC
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period', '12', 'INTEGER', false, id
FROM feature
WHERE name = 'Price Rate of Change (ROC) Indicator';
