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

-- Insertion des paramètres pour Support
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Time Interval', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Support';

-- Insertion des paramètres pour Resistance
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Time Interval', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Resistance';

-- Insertion des paramètres pour Simple Moving Average (SMA)
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Time', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Simple Moving Average (SMA)';

INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Simple Moving Average (SMA)';

-- Insertion des paramètres pour Exponential Moving Average (EMA)
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Time', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Exponential Moving Average (EMA)';

INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Exponential Moving Average (EMA)';

-- Insertion des paramètres pour MACD
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Time', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'MACD (Moving Average Convergence Divergence)';

INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period1', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'MACD (Moving Average Convergence Divergence)';

INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period2', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'MACD (Moving Average Convergence Divergence)';

-- Insertion des paramètres pour Bollinger Bands
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Time', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Bollinger Bands';

INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Bollinger Bands';

INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'k', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Bollinger Bands';

-- Insertion des paramètres pour RSI
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Time', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Relative Strength Index (RSI)';

INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'period', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Relative Strength Index (RSI)';

-- Insertion des paramètres pour Stochastic Oscillator
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Time', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Stochastic Oscillator';

INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Period', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Stochastic Oscillator';

-- Insertion des paramètres pour Price Rate of Change (ROC)
INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Time', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Price Rate of Change (ROC) Indicator';

INSERT INTO parameter_definition (name, default_value, type, required, feature_id)
SELECT 'Period', '', 'DOUBLE', true, id
FROM feature
WHERE name = 'Price Rate of Change (ROC) Indicator';
