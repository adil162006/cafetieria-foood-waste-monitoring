{{ config(materialized='view') }}

with source_records as (
    select
        safe_cast(ID as int64) as id,
        safe_cast(date as date) as waste_date,
        safe_cast(meals_served as int64) as meals_served,
        safe_cast(kitchen_staff as int64) as kitchen_staff,
        safe_cast(temperature_C as float64) as temperature_c,
        safe_cast(humidity_percent as float64) as humidity_percent,
        safe_cast(day_of_week as int64) as day_of_week,
        safe_cast(special_event as int64) as special_event,
        safe_cast(past_waste_kg as float64) as past_waste_kg,
        nullif(lower(trim(cast(staff_experience as string))), 'nan') as staff_experience_raw,
        nullif(lower(trim(cast(waste_category as string))), 'nan') as waste_category_raw,
        safe_cast(food_waste_kg as float64) as food_waste_kg
    from {{ source('raw', 'food_waste_records') }}
), normalized as (
    select
        id, waste_date,
        meals_served,
        kitchen_staff,
        temperature_c,
        humidity_percent,
        day_of_week,
        special_event,
        past_waste_kg,
        case
            when staff_experience_raw in ('beginner', 'intermediate', 'expert')
                then initcap(staff_experience_raw)
            else 'Unknown'
        end as staff_experience,
        case
            when waste_category_raw in ('meat', 'dairy', 'vegetables', 'grains')
                then initcap(waste_category_raw)
            else 'Unknown'
        end as waste_category,
        food_waste_kg
    from source_records
    where id is not null
), deduplicated as (
    select *
    from normalized
    qualify row_number() over (
        partition by id
        order by waste_date desc, food_waste_kg desc
    ) = 1
)
select *
from deduplicated
where waste_date is not null
  and food_waste_kg is not null
  and food_waste_kg >= 0
