{{ config(materialized='table') }}

select
    waste_date,
    sum(food_waste_kg) as total_food_waste_kg,
    sum(meals_served) as total_meals_served,
    safe_divide(sum(food_waste_kg), sum(meals_served)) as average_food_waste_per_meal_kg,
    avg(temperature_c) as average_temperature_c,
    avg(humidity_percent) as average_humidity_percent,
    count(*) as record_count
from {{ ref('stg_food_waste') }}
group by waste_date
