CREATE TABLE electricity_observations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    period DATE NOT NULL,

    price_area_code VARCHAR(10) NOT NULL,

    consumer_group_code VARCHAR(10) NOT NULL,

    consumption_mwh BIGINT NOT NULL,

    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT electricity_observations_consumption_non_negative
        CHECK (consumption_mwh >= 0),

    CONSTRAINT electricity_observations_unique_observation
        UNIQUE (
            period,
            price_area_code,
            consumer_group_code
        )
);