{{ config(materialized='table') }}

select
    date_trunc(waste_date, month) as waste_month,
    sum(food_waste_kg) as total_food_waste_kg,
    avg(food_waste_kg) as average_food_waste_kg,
    sum(meals_served) as total_meals_served,
    safe_divide(sum(food_waste_kg), sum(meals_served)) as waste_per_meal_kg
from {{ ref('stg_food_waste') }}
group by waste_month
