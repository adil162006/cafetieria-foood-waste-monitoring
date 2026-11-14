{{ config(materialized='table') }}

with category_totals as (
    select
        waste_category,
        sum(food_waste_kg) as total_food_waste_kg,
        avg(food_waste_kg) as average_food_waste_kg,
        count(*) as record_count
    from {{ ref('stg_food_waste') }}
    group by waste_category
)
select
    waste_category,
    total_food_waste_kg,
    average_food_waste_kg,
    record_count,
    100 * safe_divide(total_food_waste_kg, sum(total_food_waste_kg) over ()) as percent_of_total_waste
from category_totals
